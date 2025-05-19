import json
import openai
from tools.utils import save_data
from memory.json_memory import JSONMemory
from tools.location_extractor import extract_location, extract_date, extract_number, extract_return_date
from agents.flight_search_api_agent import flight_search_api_agent

import os
from dotenv import load_dotenv
import requests
import json




load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")

flight_memory = JSONMemory(os.path.join(DATA_DIR, "flight_search_data.json"))
FLIGHT_SEARCH_DATA_FILE = os.path.join(DATA_DIR, "flight_search_data.json")
pending_flight_data = {}
pending_passenger_data = {}

deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}

def save_flight_data(flight_details):
    """Ensures the flight search data file exists and saves flight details, overwriting previous data."""
    # ✅ Ensure the `data/` directory exists
    os.makedirs(os.path.dirname(FLIGHT_SEARCH_DATA_FILE), exist_ok=True)

    try:
        # ✅ Save new flight data, overwriting previous data
        with open(FLIGHT_SEARCH_DATA_FILE, "w") as f:
            json.dump(flight_details, f, indent=4)

        print("✅ Flight data successfully saved!")

    except Exception as e:
        print(f"❌ Error saving flight data: {e}")

def get_flight_type(origin, destination):
    """
    Determines if the flight is 'domestic' or 'international' based on the origin and destination airports.
    """
    domestic_airports = {
        "dhaka": "DAC",
        "chittagong": "CGP",
        "sylhet": "ZYL",
        "coxs bazar": "CXB",
        "jessore": "JSR",
        "barishal": "BZL",
        "rajshahi": "RJH",
        "saidpur": "SPD",
    }

    if not origin or not destination:  # If either is None, return unknown
        print("⚠️ Missing origin or destination. Flight type undetermined.")
        return "unknown"

    origin_lower = origin.lower().strip()
    destination_lower = destination.lower().strip()

    is_origin_domestic = origin_lower in domestic_airports
    is_destination_domestic = destination_lower in domestic_airports

    flight_type = "domestic" if is_origin_domestic and is_destination_domestic else "international"

    print(f"🟢 [DEBUG] Flight Type Determined: {flight_type} (Origin: {origin}, Destination: {destination})")
    return flight_type


def extract_flight_details(user_input: str, user_id:str):
    """
    Extracts structured flight details dynamically using NLP while retaining previous values.
    """
    global pending_flight_data

    # ✅ Load existing flight data if available
    flight_details = flight_memory.load_data() or {}

    if not isinstance(flight_details, dict):
        flight_details = {}
    # print(flight_details)
    # ✅ Ensure all required fields exist with default values
    flight_details.setdefault("origin", None)
    flight_details.setdefault("destination", None)
    flight_details.setdefault("date_of_travel", None)
    flight_details.setdefault("journey_type", None)
    flight_details.setdefault("num_adults", 1)
    flight_details.setdefault("num_children", 0)
    flight_details.setdefault("flight_type", None)
    flight_details.setdefault("return_date", None)
    flight_type = None
    # ✅ Extract new flight details
    origin = extract_location(user_input, "from")
    destination = extract_location(user_input, "to")
    date_of_travel = extract_date(user_input)
    return_date = extract_return_date(user_input)
    # ✅ Extract number of passengers (adults & children) correctly
    num_adults = extract_number(user_input, "adult") or extract_number(user_input, "adults")
    num_children = extract_number(user_input, "child") or extract_number(user_input, "children")

    if num_adults > 0:
        flight_details["num_adults"] = num_adults
    if num_children > 0:
        flight_details["num_children"] = num_children

    # ✅ Extract and update journey type
    journey_type = extract_journey_type(user_input)
    if journey_type:
        flight_details["journey_type"] = journey_type

    # ✅ Update fields only if new values are found
    if origin and origin.lower() != "unknown" and origin != 'null':
        flight_details["origin"] = origin
    if destination and destination.lower() != "unknown" and destination != 'null':
        flight_details["destination"] = destination
    if date_of_travel and date_of_travel.lower() != "unknown" and date_of_travel != None:
        flight_details["date_of_travel"] = date_of_travel
    if return_date and return_date.lower() != "unknown" and return_date != None:  # Update return_date
        flight_details["return_date"] = return_date

    if origin.lower() != "unknown" and origin.lower() !=  None and origin.lower() !=  'null' and destination.lower() != "unknown" and destination.lower() !=  None and destination.lower() !=  'null':
        flight_type = get_flight_type(origin, destination)
        flight_details["flight_type"] = flight_type

    if flight_type and flight_type.lower() != "unknown" and flight_type != None:
        flight_details["flight_type"] = flight_type

    if journey_type and journey_type.lower() != "unknown" and journey_type != None:
        flight_details["journey_type"] = journey_type

    print(flight_details)
    # ✅ Identify missing fields AFTER merging new and old values
    missing_fields = [field for field in ["origin", "destination", "date_of_travel", "journey_type"] if not flight_details[field]]

    # ✅ Save the updated flight details
    save_flight_data(flight_details)

    if not missing_fields:
        print("🚀 Calling flight_search_api_agent() to fetch flight data...")
        if flight_type and flight_type.lower() != "unknown" and flight_type != None:
            if flight_details["origin"].lower() != "unknown" and flight_details["origin"].lower() != None and flight_details["origin"].lower() != 'null' and flight_details["destination"].lower() != "unknown" and flight_details["destination"].lower() != None and flight_details["destination"].lower() != 'null':
                flight_type = get_flight_type(flight_details["origin"], flight_details["destination"])
                flight_details["flight_type"] = flight_type

        flight_list = flight_search_api_agent()

        if isinstance(flight_list, str):  # If API returns an error
           # return f"📌 Flight List Data: \n{flight_list}"
           return flight_list

        print(f"✅ Flight search details saved successfully: {flight_details}")
        print(f"📌 Flight List Data: {flight_list}")
        print("Flight details saved! Please ask about available flights.")
        return flight_list
    missing_response = ask_for_missing_details_gpt4(flight_details, missing_fields, user_input)
    return missing_response
    # return f"✈️ Almost done! Please provide: {', '.join(missing_fields)}."

def ask_for_missing_details_gpt4(flight_details, missing_details, user_message):
    """
    Uses GPT-4 to generate dynamic, human-like responses asking for missing flight details.
    """
    client = openai.Client(api_key=OPENAI_API_KEY)
    prompt = (
        f"You are a friendly AI travel assistant helping a user book a flight."
        f"\n\n### User Message:\n{user_message}"
        f"\n\n### Known Details:\n{json.dumps(flight_details, indent=2)}"
        f"\n\n### Missing Details: {', '.join(missing_details)}"
        f"\n\nCreate a **short, warm response** that acknowledges the known details "
        f"and asks only for the missing details in a **casual and natural way**."
        f"Please give very specific answer in one sentence."
    )

    # print(prompt)
    # # ✅ Use OpenAI v1.0.0+ API
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": "You are a helpful travel assistant."},
    #         {"role": "user", "content": prompt},
    #     ],
    #     max_tokens=50,
    #     temperature=0.8,
    # )
    #
    # # ✅ Extract and return response text
    # response_text = response.choices[0].message.content.strip()
    # print(response_text)
    # return response_text

    payload = {
        "model": "deepseek-chat",  # Replace with the correct model name
        "messages": [
            {"role": "system", "content": "You are a helpful travel assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 200,
        "temperature": 0.8,
    }
    # Make the API request
    response = requests.post(DEEPSEEK_API_URL, headers=deepseek_headers, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"].strip()
        print(response_text)
        return response_text
    else:
        print(f"Error: {response.status_code}, {response.text}")


def extract_journey_type(user_input: str) -> str:
    """
    Determines the journey type based on keywords.
    Returns "OneWay" if only one date is mentioned,
    and "RoundTrip" if words like 'round trip' or a return date is present.
    """
    user_input = user_input.lower()
    # Keywords for round trip
    round_trip_keywords = ["round trip", "return", "coming back", "two way", "round"]
    # Check for round trip indicators
    if any(keyword in user_input for keyword in round_trip_keywords):
        return "RoundTrip"
    # If no return date and no round trip indicators, assume OneWay
    return "OneWay"

