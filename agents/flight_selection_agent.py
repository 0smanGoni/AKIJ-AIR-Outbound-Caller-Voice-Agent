import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from memory.json_memory import JSONMemory
from dotenv import load_dotenv
import requests


# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize LLM Model
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")

SELECTED_FLIGHT_FILE = os.path.join(DATA_DIR, "selected_flight.json")
FLIGHT_LIST_FILE = os.path.join(DATA_DIR, "flight_list.json")
flight_memory = JSONMemory(os.path.join(DATA_DIR, "flight_search_data.json"))
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "apikey": os.getenv("API_KEY"),
    "secretecode": os.getenv("SECRET_CODE")
}

def flight_selection_agent(user_message: str):
    """
    Uses LLM (GPT-4) to intelligently select a flight based on user input.
    Saves selected flight details in `selected_flight.json`.
    Returns the flight_key and tracking_id.
    """

    # ✅ Load flight list
    try:
        with open(FLIGHT_LIST_FILE, "r") as f:
            flight_data = json.load(f)
    except FileNotFoundError:
        return "❌ No flight data available. Please search for flights first."

    flight_list = flight_data.get("data", [])
    if not flight_list:
        return "❌ No flights found."

    # ✅ Extract tracking ID for fallback
    correct_tracking_id = flight_list[0]["tracking_id"] if flight_list else "UNKNOWN_TRACKING_ID"

    # ✅ Prepare System Prompt & Context
    system_prompt = "You are a flight assistant that selects the best flight based on user queries."
    context = f"""
    You are given a list of flights. Select the best flight based on the user’s query.

    **User Query:** "{user_message}"

    **Flight Data:**
    {json.dumps(flight_list, indent=2)}

    Your task is to select a flight and return **ONLY a valid JSON** in this format:
    {{
        "flight_id": "<selected_flight_id>",
        "tracking_id": "<tracking_id>",
        "flight_key": "<flight_key>",
        "price": <price>,
        "departure_departure_time": "<departure_time>",
        "arrival_departure_time": "<arrival_time>",
        "cabin_class": "<cabin_class>",
        "carrier_operating": "<carrier>",
        "connecting_airport": <connecting_airport_list>
    }}

    **Rules:**
    - If the user says **"first option"**, return the **first flight**.
    - If the user says **"second option"**, return the **second flight**.
    - If the user asks for **cheapest**, return the **lowest price flight**.
    - If the user asks for **shortest duration**, return the **fastest flight**.
    - If the user specifies an **airline**, return the flight from that airline.
    - Always return **valid JSON** only. No extra text.
    """

    # ✅ Generate response using LLM
    response = llm.invoke([HumanMessage(content=context)])
    # ✅ Debug: Print raw response to check if it's valid JSON
    # print("🔍 RAW RESPONSE FROM LLM:", response.content.strip().strip("```json").strip("```"))
    # ✅ Validate JSON response
    try:
        selected_flight = json.loads(response.content.strip().strip("```json").strip("```"))
        flight_key = selected_flight.get("flight_key")
        tracking_id = selected_flight.get("tracking_id")
        validate_flight_response = json.loads(validate_flight(flight_key, tracking_id))
        booking_tracking_id = validate_flight_response.get("booking_tracking_id")
        if booking_tracking_id:
            selected_flight["booking_tracking_id"] = booking_tracking_id
        else:
            reason = validate_flight_response.get("reason")
            return f"Please select another flight. Reason: {reason}"
    except json.JSONDecodeError:
        return "❌ Error processing flight selection. Invalid JSON format."

    # ✅ Save selected flight to file
    os.makedirs(os.path.dirname(SELECTED_FLIGHT_FILE), exist_ok=True)
    if validate_flight_response.get("status") == "success":
        with open(SELECTED_FLIGHT_FILE, "w") as f:
            json.dump(selected_flight, f, indent=4)

    return format_flight_details(selected_flight)

def format_flight_details(flight):
    """
    Formats the flight details into a beautifully structured output.
    """
    flight_details = flight_memory.load_data() or {}
    flight_type = flight_details["flight_type"]
    if flight_type == "domestic":
        user_message = "✅  Please upload your NID (.jpg or .jpeg format) or Entry information Manually."
    else:
        user_message = "✅  Please upload your Passport (.jpg or .jpeg format) or Entry information Manually."

    return f"""
    ✈️ Flight Selection Successful!  
    --------------------------------------  
    Flight ID: {flight["flight_id"]}  
    Tracking ID: {flight["tracking_id"]} 
    Price: ${flight["price"]} 
    Departure Time: {flight["departure_departure_time"]}  
    Arrival Time: {flight["arrival_departure_time"]}  
    Cabin Class: {flight["cabin_class"]} 
    Carrier: {flight["carrier_operating"]}
    Connecting Airports: {", ".join(flight["connecting_airport"]) if flight["connecting_airport"] else "Direct Flight"}  
    ✅  Your flight has been successfully selected!
    {user_message}
    """

def validate_flight(flight_key, tracking_id):
    """
    Validate the selected flight with the backend system.
    """
    try:
        validate_url = "https://serviceapi.innotraveltech.com/flight/validate"
        validate_payload = {
            "member_id": "2",
            "result_type": "general",
            "data": [
                {
                    "tracking_id": tracking_id,
                    "flight_key": flight_key,
                    "brand_option": ""
                }
            ]
        }
        response = requests.post(validate_url, headers=headers, json=validate_payload)
        response.raise_for_status()
        validate_data = response.json()

        return json.dumps(validate_data)

    except Exception as ex:
        print(f"❌ Exception in validate_flight: {ex}")
        return f"Please select another flight"

