import json
import os
import re

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize GPT-4 Model
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# ✅ Predefined Examples for Classification
examples = {
    "greeting": [
        "hi", "hello", "Hey!", "Good morning", "Good evening", "Assalamualaikum",
        "Bonjour!", "Hola!", "Namaste", "Konnichiwa!", "Howdy!", "Yo!", "What's up?",
        "Greetings!", "Salam!", "Hi chatbot!", "Hello AI!", "Hey there!", "Nice to meet you!"
    ],
    "flight_booking": [
        "I want to book a flight", "Book a flight",
        "I need to book a flight to Tokyo", "Can you help me book a ticket to London?",
        "I am looking for a flight to Paris", "Book me a flight from Dubai to Singapore",
        "I want to go to New York from Los Angeles", "I need a round-trip ticket to Sydney",
        "Reserve a flight from Madrid to Rome", "Get me a first-class ticket to Berlin",
        "I want to fly to Hong Kong next Monday", "I’d like to travel to Istanbul next week",
        "Can you book me a direct flight to Singapore?", "I’m searching for flights to Toronto",
        "Are there any flights available to Bangkok tomorrow?", "I want a business class seat to Frankfurt",
        "Please find me an economy flight from Chicago to Miami", "one way trip", "OneWay", "Round Trip"
    ],
    "providing_date": [
        "I will arrive on February 15th", "My flight should be on July 20",
        "Can I book a flight for December 24?", "I want to fly on the 1st of May",
        "The best departure date for me is November 18", "I’m planning for April 3",
        "The event is scheduled for March 10", "I’m available from 27th February to 5th March",
        "Traveling on September 10, do you have flights?", "Departing on June 5, returning June 12",
        "I prefer to travel in early January", "I need a ticket for next Wednesday",
        "Can I fly on Sunday evening?", "I need a morning flight for April 8",
        "Looking for flights in the first week of October"
    ],
    "providing_location": [
        "Flying from New York to Los Angeles", "Departing from Paris to Berlin",
        "I want to go from Dhaka to Sylhet", "Leaving from Miami to Mexico City",
        "I’m traveling from Sydney to Auckland", "I will be flying from Toronto to Vancouver",
        "Flying out of Amsterdam to Brussels", "Can I get a ticket from Cairo to Dubai?",
        "My departure city is Jakarta", "I will be landing in Madrid",
        "Traveling to Bangkok, can you help?", "From San Francisco, going to Seoul",
        "I want to go to Buenos Aires from Lima", "I’ll be leaving from Manila to Tokyo",
        "Flying from Istanbul, landing in London"
    ],
    "passenger_details": [
        "My name is Alice Johnson", "I need a ticket for John Doe",
        "Passenger: Daniel Cooper, Phone: 01712345678", "Book a flight for Sarah Lee, Passport: B123456",
        "James Brown, Email: james@example.com", "Reservation for Michelle Adams, Passport: Z987654",
        "My name is Ibrahim Khalil, Phone: 01750671424", "I am Kevin Lee, Email: kevin@example.com",
        "I need to add passenger details: Name: Alex White, Passport: T123456",
        "Can you save these details? Name: Oliver Martinez, Contact: 01789012345",
        "My booking includes Emily Scott, Email: emily@travel.com",
        "Passenger details: Name: Amelia Watson, Passport: L765432",
        "My wife is traveling with me, her name is Julia Carter",
        "The passenger for this ticket is Richard Henry, Email: richard@mail.com",
        "Please save my info: Mark Evans, Phone: 01892345678, Email: mark@example.net",
    ],
    "flight_query": [
        "What is the cheapest flight to Dubai?",
        "Are there any flights available from New York to London tomorrow?",
        "How long is the flight from Paris to Tokyo?",
        "Which airlines operate flights from Los Angeles to Sydney?",
        "Can you check flight prices for next weekend?",
        "I need a list of flights departing from Berlin on Friday.",
        "Are there direct flights from Toronto to Madrid?",
        "What’s the best time to book a flight to Singapore?",
        "How much does a business-class ticket to Rome cost?",
        "Do you have flight options for a round trip to Bangkok?",
        "I want to see flights with baggage included.",
        "What airlines have flights from Dhaka to Dubai?",
        "Can you check the available flights for the next week?",
        "Tell me the flight duration from London to New York."
    ],
    "flight_selection": [
        "I will take the first option.",
        "Book the second flight from the list.",
        "I want to choose the Emirates flight.",
        "Select the flight departing at 10 AM.",
        "I'll go with the cheapest option.",
        "I want to book the business class ticket from the list.",
        "Choose the flight that has the shortest duration.",
        "I'll take the flight with baggage included.",
        "Select the non-stop flight to New York.",
        "I want the third flight option.",
        "Can you book me the flight with Qatar Airways?",
        "Pick the one with the best departure time.",
        "I'll take the round-trip flight with the best price.",
        "I want to book this flight"
    ],
    "booking_confirmation": [
        "Yes, confirm my booking.",
        "I want to finalize my reservation.",
        "Please proceed with the booking.",
        "Confirm my flight ticket.",
        "Everything looks good, go ahead with the booking.",
        "I am ready to book now.",
        "Yes, book the selected flight.",
        "I want to complete the payment and confirm.",
        "Confirm the reservation for me.",
        "Go ahead and issue the ticket.",
        "Yes, please proceed with the final booking.",
        "All details are correct, confirm the booking.",
        "Finalize my flight ticket now.",
        "I want to complete my booking.",
        "Yes, confirm it.",
        "Go ahead with the booking.",
        "Yes, proceed with confirmation.",
        "Confirm my flight.",
        "Book it now.",
    ],
    "file_upload": [
        "Upload passport/NID",
        "Upload my passport",
        "I need to upload my NID",
        "Upload my ID card",
        "Can I upload my travel documents?",
        "I want to upload my visa copy",
        "Upload my passport or NID",
        "Upload files for booking",
        "Here’s my scanned passport, please upload",
        "I am uploading my passport now",
        "Uploading my identity documents",
        "I need to submit my passport details, where can I upload?",
        "How do I upload my ID proof?",
        "Send my passport details",
        "Upload my verification document",
        "Upload my travel document",
        "I need to attach my identification proof",
        "Attach my passport copy for verification",
        "Here is my scanned passport, please proceed",
        "Uploading my ID now"
    ],
    "passenger_info_manual_entry": [
        "Enter passenger details manually",
        "I will enter my details myself",
        "Fill in my information manually",
        "I don’t want to upload, I will enter my details",
        "Let me type my personal details",
        "I'll manually input my information",
        "Enter my passport details manually",
        "I will provide my personal details one by one",
        "I prefer to enter my details instead of uploading",
        "I want to input my own details",
        "Type my name and contact manually",
        "I'll add my passport number myself",
        "Let me type my booking details",
        "I want to manually provide my travel information",
        "Skip file upload, I will enter details instead",
        "Enter information manually"
    ],
    "other": [
        "What is the weather like in New York?", "I need assistance with my luggage",
        "Can you recommend a good hotel in Rome?", "What are the baggage policies for Qatar Airways?",
        "What are the COVID travel restrictions?", "How early should I arrive at the airport?",
        "Can you check the flight status for Emirates?", "Is there an airport lounge at JFK?",
        "What documents do I need for international travel?", "Can I carry extra baggage?",
        "How much does additional luggage cost?", "Can I get a meal preference on my flight?",
        "Are pets allowed on flights?", "Do airlines provide WiFi on long-haul flights?",
        "What are the best tourist attractions in Singapore?"
    ]

}


def clean_json_response(response_text):
    """
    Cleans and extracts valid JSON from GPT-4 responses.
    Removes markdown formatting, triple backticks, and extra whitespace.
    """
    # Remove triple backticks and markdown artifacts
    response_text = re.sub(r"```json\n?|```", "", response_text).strip()

    # Ensure the text is a valid JSON format
    try:
        parsed_json = json.loads(response_text)
        return parsed_json if isinstance(parsed_json, dict) else {"intent": "other"}
    except json.JSONDecodeError:
        print(f"❌ JSON Parse Error: {response_text}")
        return {"intent": "other"}  # Fallback in case of invalid JSON


def detect_intent(user_input):
    """
    Uses GPT-4 to classify user input into predefined categories with strict JSON formatting.
    """
    try:
        response = llm.invoke([
            HumanMessage(
                content=f"""
                You are an AI classifier. Your task is to categorize user input into one of these categories:

                - 'greeting': When the user greets (e.g., {json.dumps(examples["greeting"])}).
                - 'flight_booking': When the user asks to book a flight (e.g., {json.dumps(examples["flight_booking"])}).
                - 'providing_date': When the user provides a travel date (e.g., {json.dumps(examples["providing_date"])}).
                - 'providing_location': When the user provides a location (e.g., {json.dumps(examples["providing_location"])}).
                - 'flight_query': When the user provides a location (e.g., {json.dumps(examples["flight_query"])}).
                - 'flight_selection': When the user provides a location (e.g., {json.dumps(examples["flight_selection"])}).
                - 'booking_confirmation': When the user provides a location (e.g., {json.dumps(examples["booking_confirmation"])}).
                - 'file_upload': When the user mentions uploading a passport, NID, or other files (e.g., {json.dumps(examples["file_upload"])}).
                - 'passenger_info_manual_entry': When the user requests to enter their details manually instead of uploading files (e.g., {json.dumps(examples["passenger_info_manual_entry"])}).
                - 'other': When none of the above applies (e.g., {json.dumps(examples["other"])}).
                

                Additional Rules:
                - If the user mentions **both origin and destination**, classify as 'flight_booking'.
                - If the user mentions **only one location**, classify as 'providing_location'.
                - If the user provides **only a date**, classify as 'providing_date'.
                - If the user provides **name, email, phone, or passport**, classify as 'passenger_details'.
                - If the user is asking about **flight details, ticket prices, flight duration, airline options, or availability**, classify as 'flight_query'.
                - If the user is selecting a flight from a provided list, classify as 'flight_selection'.
                - If the user confirms their booking, classify as 'booking_confirmation'.
                - If the user mentions **uploading passport, NID, or other files**, classify as 'file_upload'.
                - If the user says **they want to enter details manually**, classify as 'passenger_info_manual_entry'.
                - If unsure, classify as 'other'.

                Format your response strictly as JSON:
                {{"intent": "<category>"}}

                User Input: "{user_input}"
                """
            )
        ])

        if response and hasattr(response, "content"):
            response_text = response.content.strip()

            # ✅ Ensure response is valid JSON
            try:
                intent_data = clean_json_response(response_text)
                intent = intent_data.get("intent", "other").lower()
                valid_intents = {
                    "greeting", "flight_booking", "providing_date",
                    "providing_location", "passenger_details", "flight_query",
                    "flight_selection", "booking_confirmation", "file_upload",
                    "passenger_info_manual_entry", "other"
                }
                return intent if intent in valid_intents else "other"

            except json.JSONDecodeError:
                print(f"❌ Invalid JSON Response: {response_text}")
                return "other"

        else:
            print("❌ GPT-4 Response is Empty")
            return "other"

    except Exception as e:
        print(f"❌ GPT-4 Intent Extraction Failed: {e}")
        return "other"
