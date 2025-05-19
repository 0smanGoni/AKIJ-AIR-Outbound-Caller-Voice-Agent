import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize LLM Model
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")

FLIGHT_LIST_FILE = os.path.join(DATA_DIR, "flight_list.json")

def flight_query_agent(user_message: str):
    """
    Uses LLM (GPT-4) to generate human-like answers for any flight-related query.
    """

    # ✅ Load flight list
    try:
        with open(FLIGHT_LIST_FILE, "r") as f:
            flight_data = json.load(f)
    except FileNotFoundError:
        return "❌ No flight data available. Please try again later."

    if isinstance(flight_data, list):
        flight_list = flight_data
    else:
        flight_list = flight_data.get("data", [])
    if not flight_list:
        return "❌ No flights found."

    # ✅ Prepare System Prompt & Context
    system_prompt = "You are an expert travel assistant who answers flight-related questions in a natural, engaging manner."
    context = f"""
    You have access to real-time flight data. Your job is to **accurately answer any flight-related question** in a friendly, conversational way.

    **User Query:** "{user_message}"

    **Available Flight Data:**
    {flight_list}

    **How You Should Respond:**
    - If the user asks for the **cheapest flight**, respond:  
      "The cheapest flight available is {{airline}} for ${{price}}, departing on {{date}} at {{departure_time}}."
    - If the user asks for **flight duration**, respond:  
      "The flight from {{origin}} to {{destination}} takes approximately {{duration}}."
    - If the user asks about **available airlines**, respond:  
      "Flights are available from {{airline_list}}."
    - If the user asks for **baggage information**, respond:  
      "This flight includes {{baggage_allowance}} baggage allowance."
    - If the user asks for **layovers**, respond:  
      "This flight has a layover in {{layover_city}} for {{layover_time}}."
    - If the user asks about **business class or economy options**, respond:  
      "Business class for this route costs around ${{business_class_price}}. Economy is available for ${{economy_price}}."
    - If the user asks for **flight options next week**, respond:  
      "We have {{flight_count}} flights available for next week, starting from ${{lowest_price}}."
    - If the user asks **general travel questions**, provide **helpful, friendly advice**.

    **Rules:**
    - Responses must be **engaging, clear, and natural**.
    - Provide **full, human-like sentences** instead of raw data.
    - **DO NOT** return JSON data.
    - **DO NOT** say "I don't know" — always provide relevant travel insights.
    """

    # ✅ Generate response using LLM
    response = llm.invoke([HumanMessage(content=context)])

    # ✅ Return the natural language response
    return response.content.strip()
