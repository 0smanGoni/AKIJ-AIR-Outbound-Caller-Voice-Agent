import re
import os
import requests
from typing import Optional, Tuple
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.tools import StructuredTool
from langchain.memory import ConversationBufferMemory
from memory.json_memory import JSONMemory
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from tools.utils import get_current_time
from tools.detect_intent import detect_intent
from agents.flight_search_agent import extract_flight_details
from agents.flight_selection_agent import flight_selection_agent
from agents.flight_query_agent import flight_query_agent
from agents.confirm_booking_agent import confirm_booking_agent
from agents.passenger_details_agent import collect_passenger_details, extract_passenger_details
from agents.smart_assistant_agent import smart_assistant_agent
from dotenv import load_dotenv


# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize GPT-4o Model
llm = ChatOpenAI(model="gpt-4o")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")  # Set the data folder inside the project

# Ensure the 'data' folder exists
os.makedirs(DATA_DIR, exist_ok=True)

# ✅ Memory for conversation history
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
passenger_memory = JSONMemory(os.path.join(DATA_DIR, "passenger_data.json"))
flight_memory = JSONMemory(os.path.join(DATA_DIR, "flight_search_data.json"))

# ✅ Define Schemas for Structured Tools
class TimeInputSchema(BaseModel):
    pass  # No input required for time retrieval

class FlightSearchInputSchema(BaseModel):
    origin: str
    destination: str
    date_of_travel: str
    journey_type: str
    num_adults: int
    num_children: int
    flight_type: str

class PassengerDetailsInputSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    passport_number: str

# ✅ Define Structured Tools
tools = [
    StructuredTool(
        name="Time",
        func=get_current_time,
        description="Provides the current time.",
        args_schema=TimeInputSchema
    ),
    StructuredTool(
        name="FlightSearch",
        func=extract_flight_details,
        description="Collects flight search details dynamically.",
        args_schema=FlightSearchInputSchema
    ),
    StructuredTool(
        name="PassengerDetails",
        func=collect_passenger_details,
        description="Collects passenger details dynamically.",
        args_schema=PassengerDetailsInputSchema
    )
]

# ✅ Load structured chat prompt
try:
    prompt = hub.pull("hwchase17/structured-chat-agent")
except:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly AI assistant."),
        ("user", "{input}")
    ])

# ✅ Create Agents
greet_agent = create_structured_chat_agent(llm=llm, tools=[], prompt=prompt)
flight_search_agent = create_structured_chat_agent(llm=llm, tools=[tools[1]], prompt=prompt)
passenger_details_agent = create_structured_chat_agent(llm=llm, tools=[tools[2]], prompt=prompt)

def select_agent(user_input, user_id, file_upload=None):
    from app import log_conversation

    """
    Dynamically selects the appropriate agent based on LLM intent classification.
    """
    # Step 1: Detect Intent
    if isinstance(user_input, bytes):  # Check if input is bytes (voice input)
        user_input = user_input.decode("utf-8")

    intent = detect_intent(user_input)
    # Debugging logs
    print(f"🗣️ User Intent Detected: {intent}")

    # Define default response & next steps
    response = "I'm not sure how to handle that."
    suggested_keywords = []

    if intent == "greeting":
        response = "Hello! How can I assist you today?"
        suggested_keywords = ["Book a flight"]

    elif intent == "flight_booking":
        response = extract_flight_details(user_input, user_id)
        suggested_keywords = []

    elif intent == "providing_date":
        response = extract_flight_details(user_input, user_id)
        suggested_keywords = []

    elif intent == "providing_location":
        response = extract_flight_details(user_input, user_id)
        suggested_keywords = []

    elif intent == "passenger_details":
        # ✅ Load flight search data
        flight_details = flight_memory.load_data() or {}
        num_adults = flight_details.get("num_adults", 1)
        num_children = flight_details.get("num_children", 0)
        total_passengers = num_adults + num_children
        flight_type = flight_details.get("flight_type", "domestic")  # Default: domestic

        # ✅ Load existing passenger data
        passenger_details = passenger_memory.load_data() or {"passengers": []}

        # ✅ Define required fields based on flight type
        if flight_type == "domestic":
            required_fields = ["title", "gender", "first_name", "last_name", "email", "phone", "dob"]
        else:
            required_fields = ["title", "gender", "first_name", "last_name", "email", "phone", "dob", "passport_number",
                               "nationality", "date_of_issue", "date_of_expiry"]

        # ✅ Find the next passenger with missing details
        passenger_index = 0
        for i, passenger in enumerate(passenger_details.get("passengers", [])):
            if not all(passenger.get(field) for field in required_fields):
                passenger_index = i
                break
        else:
            if len(passenger_details.get("passengers", [])) >= total_passengers:
                response = "All passengers' details have already been collected."
                suggested_keywords = ["Select flight", "Confirm booking", "View itinerary"]
                log_conversation(user_id, user_input, response)
                return {"response": response, "next_steps": suggested_keywords}

            passenger_index = len(passenger_details.get("passengers", []))

        # ✅ Extract Passenger Data
        extracted_data = extract_passenger_details(user_input)

        # ✅ Call Passenger Details Agent with flight type
        response = collect_passenger_details(
            passenger_index=passenger_index,
            flight_type=flight_type,
            **extracted_data  # Pass all extracted fields as keyword arguments
        )

        suggested_keywords = ["Proceed to booking", "Confirm Booking"]

    elif intent == "flight_query":
        response = flight_query_agent(user_input)
        suggested_keywords = ["View available flights", "Check baggage allowance", "See airline policies"]

    elif intent == "flight_selection":
        response = flight_selection_agent(user_input)
        suggested_keywords = ["Upload passport/NID", "Enter Information Manually"]

    elif intent == "confirm_booking" or intent == "booking_confirmation":
        print("Calling confirm_booking_agent...")
        response = confirm_booking_agent()
        suggested_keywords = []

    elif intent == "other":
        response = smart_assistant_agent(user_input, user_id)
        suggested_keywords = ["Ask about loyalty programs", "Check refund policy", "Speak to a support agent"]

    elif intent == "file_upload":
        response = "Please upload files in jpeg or jpg format."
        suggested_keywords = []
    elif intent == "passenger_info_manual_entry":
        response = "Please enter your information manually. for example, (My name is Adam Foster adam@gmail.com 01856684559)"
        suggested_keywords = []

    # ✅ Log the conversation
    log_conversation(user_id, user_input, response)

    return {"response": response, "next_steps": suggested_keywords}
