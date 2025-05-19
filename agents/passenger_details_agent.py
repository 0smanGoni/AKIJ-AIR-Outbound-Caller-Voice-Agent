import json
import re
from memory.json_memory import JSONMemory
from typing import Optional
import openai
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}

# Constants for field names and patterns
FIRST_NAME = "first_name"
LAST_NAME = "last_name"
EMAIL = "email"
PHONE = "phone"
PASSPORT_NUMBER = "passport_number"
PASSENGERS = "passengers"

# Updated patterns
# NAME_PATTERN = r"(?:my name is |^)([A-Za-z]+)[,\s]+([A-Za-z]+)"
NAME_PATTERN = r"(?:my name is |^)(?P<title>Mr|Mrs|Ms|Dr)\s+(?P<first_name>[A-Za-z]+)\s+(?P<last_name>[A-Za-z]+(?:\s[A-Za-z]+)*)"
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
PHONE_PATTERN = r"\b01\d{9}\b"
PASSPORT_PATTERN = r"\b[A-Z]\d{5,}\b"


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")

passenger_memory = JSONMemory(os.path.join(DATA_DIR, "passenger_data.json"))
flight_memory = JSONMemory(os.path.join(DATA_DIR, "flight_search_data.json"))  # Load flight search data

client = openai.OpenAI()

def get_total_passengers():
    """Retrieves total number of passengers (adults + children) from flight search data."""
    flight_details = flight_memory.load_data() or {}
    num_adults = flight_details.get("num_adults", 1)
    num_children = flight_details.get("num_children", 0)
    return num_adults + num_children  # Total passengers

def initialize_passenger_data(total_passengers: int, flight_type: str):
    """
    Initializes the passenger data with `null` or `None` values for all fields.
    """
    passenger_details = {PASSENGERS: []}
    for _ in range(total_passengers):
        passenger_data = {
            "title": None,
            "gender": None,
            "first_name": None,
            "last_name": None,
            "email": None,
            "phone": None,
            "dob": None
        }
        if flight_type != "domestic":
            passenger_data.update({
                "passport_number": None,
                "nationality": None,
                "date_of_issue": None,
                "date_of_expiry": None
            })
        passenger_details[PASSENGERS].append(passenger_data)
    return passenger_details

def collect_passenger_details(passenger_index: int, flight_type: str, **kwargs):
    """
    Collects passenger details dynamically and updates the passenger data.
    """
    # ✅ Load existing passenger data
    passenger_details = passenger_memory.load_data() or {"passengers": []}

    # ✅ Ensure passenger list exists and matches total passengers
    total_passengers = get_total_passengers()
    if len(passenger_details.get("passengers", [])) < total_passengers:
        passenger_details["passengers"] = [{} for _ in range(total_passengers)]

    # ✅ Ensure passenger_index is within the range
    if passenger_index >= total_passengers:
        return f"❌ Passenger index {passenger_index} is out of range."

    # ✅ Fetch the current passenger data
    passenger_data = passenger_details["passengers"][passenger_index]

    # ✅ Define required fields based on flight type
    if flight_type == "domestic":
        required_fields = ["title", "gender", "first_name", "last_name", "email", "phone", "dob"]
    else:
        required_fields = ["title", "gender", "first_name", "last_name", "email", "phone", "dob", "passport_number", "nationality", "date_of_issue", "date_of_expiry"]

    # ✅ Update fields only if new values are provided
    for field in required_fields:
        if kwargs.get(field):
            passenger_data[field] = kwargs[field]

    # ✅ Save the updated passenger details
    passenger_memory.save_data(passenger_details)

    # ✅ Identify missing fields
    missing_fields = [field for field in required_fields if not passenger_data.get(field)]

    if not missing_fields:
        passenger_summary = _get_summary(passenger_data)
        return f"🛂 {passenger_summary}"

    return f"📝 Almost done! Please provide: {', '.join(missing_fields)} for Passenger {passenger_index + 1}."

def extract_passenger_details(text):
    """Extracts passenger details (name, email, phone, passport number, etc.) from text."""
    first_name, last_name, email, phone, passport = None, None, None, None, None
    title, gender, dob, nationality, date_of_issue, date_of_expiry = None, None, None, None, None, None

    # # Extract name
    # name_match = re.search(NAME_PATTERN, text, re.IGNORECASE)
    # if name_match:
    #     first_name = name_match.group(1).strip()
    #     last_name = name_match.group(2).strip()
    # Extract name
    name_match = re.search(
        r"(?:my name is\s+)?\b(Mr|Ms|Mrs|Dr)?\b\s*([A-Z][a-z]+)[,\s]+([A-Z][a-z]+)(?:\s+(Mr|Ms|Mrs|Dr))?", text,re.IGNORECASE)
    if name_match:
        # Correct title detection (before or after)
        title = name_match.group(1) or name_match.group(4)  # Handles both title positions
        first_name = name_match.group(2).strip()
        last_name = name_match.group(3).strip()

    if title is None or title == "" or title == "null" or title == "Unknown":
        title = _analyze_title(first_name)



    # Extract email
    email_match = re.search(EMAIL_PATTERN, text)
    if email_match:
        email = email_match.group(0)

    # Extract phone number
    phone_match = re.search(PHONE_PATTERN, text)
    if phone_match:
        phone = phone_match.group(0)

    # Extract passport number
    passport_match = re.search(PASSPORT_PATTERN, text)
    if passport_match:
        passport = passport_match.group(0)

    # # Extract additional fields (example patterns, adjust as needed)
    # title_match = re.search(r"\b(Mr|Ms|Mrs|Dr)\b", text, re.IGNORECASE)
    # if title_match:
    #     title = title_match.group(0)

    gender_match = re.search(r"\b(Male|Female|Other)\b", text, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(0)

    if gender is None or gender == "" or gender == "null" or gender == "Unknown":
        gender = _analyze_gender(first_name)

    # Extract date of birth (dob) in YYYY-MM-DD format
    dob_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if dob_match:
        dob = dob_match.group(0)

    nationality_match = re.search(r"\b[A-Za-z]+\b", text)  # Nationality
    if nationality_match:
        nationality = nationality_match.group(0)

    # Add more patterns for date_of_issue and date_of_expiry if needed

    return {
        "title": title,
        "gender": gender,
        "first_name": clean_text(first_name),
        "last_name": clean_text(last_name),
        "email": email,
        "phone": phone,
        "dob": dob,
        "passport_number": passport,
        "nationality": nationality,
        "date_of_issue": date_of_issue,
        "date_of_expiry": date_of_expiry
    }

def _analyze_title(first_name):
    """
    Determines the title (Mr./Ms.) based on the first name using GPT-4.
    """
    if not first_name or first_name.strip() == "":
        return "Mr."  # Default to Mr. if name is missing or blank

    prompt = (
        f"Determine whether the following first name belongs to a male or female: {first_name}.\n"
        "Respond only with 'Mr.' for male names and 'Ms.' for female names. "
        "If uncertain, respond with 'Mr.'."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=5,
            temperature=0.5,
        )
        title = response.choices[0].message.content.strip()
        return title if title in {"Mr.", "Ms."} else "Mr."  # Default to Mr. if uncertain
    except Exception as e:
        print(f"Error in _analyze_title: {e}")
        return "Mr."  # Fallback to Mr. if GPT fails

def _analyze_gender(name):
    prompt = f"""
    You are an expert in name-based gender identification.

    - Determine the gender of the given name: '{name}'.
    - If the name is commonly associated with males, return `"male"`.
    - If the name is commonly associated with females, return `"female"`.
    - If the name is gender-neutral or ambiguous, **still choose either "male" or "female"** based on the closest match.
    - **Never return "unknown".**
    - **Strictly return only JSON, no explanations.**

    **Output must be a strict JSON object:**  
    Example:
    {{"gender": "male"}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You analyze names and return gender as structured JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.5,
            # response_format={"type": "json_object"},  # ✅ Fixed: Changed "json" to "json_object"
        )

        response_data = response.choices[0].message.content  # Since response_format is JSON, it's already a dict
        response_data = json.loads(response_data)
        return response_data.get("gender", "male")  # Default fallback is "male" if anything goes wrong

    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return "male"  # Fallback for API errors

def clean_text(text):
    """
    Removes special characters (., -, _, extra spaces) from the given text.
    Keeps only letters and spaces.
    """
    if text:
        text = re.sub(r"[^a-zA-Z\s]", "", text)  # Remove all non-alphabet characters except spaces
        text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text

def calculate_age(date_of_birth):
    current_year = datetime.now().year
    birth_year = int(date_of_birth.split("-")[0])
    return current_year - birth_year

def _get_summary(passenger_data):
    # # Construct the prompt for multiple passengers
    # passenger_summaries = []
    # for passenger in passenger_data:
    #     # age = calculate_age(passenger["date_of_birth"])
    #     summary = f"""
    #     **Passenger Summary:**
    #     - Title: {passenger["title"]}
    #     - Full Name: {passenger["full_name"]}
    #     - Gender: {passenger["gender"]}
    #     - Email: {passenger["email"]}
    #     - Phone Number: {passenger["phone_number"]}
    #     - Date of Birth: {passenger["date_of_birth"]}
    #     """
    #     passenger_summaries.append(summary)
    #
    # # Combine all summaries into one prompt
    # combined_summaries = "\n".join(passenger_summaries)
    # prompt = f"""
    # Generate a **short and specific** passenger summary for each passenger. Include only the following details for each passenger:
    # - Title
    # - Full Name
    # - Gender
    # - Email
    # - Phone Number
    # - Date of Birth
    #
    # Format the output as:
    # **Passenger Summary:**
    # - Title: <title>
    # - Full Name: <full_name>
    # - Gender: <gender>
    # - Email: <email>
    # - Phone Number: <phone_number>
    # - Date of Birth: <date_of_birth>
    #
    # Passenger Data:
    # {combined_summaries}
    # """
    #
    # # Define the payload for the API request
    # payload = {
    #     "model": "deepseek-model-name",  # Replace with the actual model name
    #     "messages": [
    #         {"role": "system", "content": "You generate concise and professional passenger summaries."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     "max_tokens": 200,  # Adjusted for multiple passengers
    #     "temperature": 0.3  # Lower temperature for more specific responses
    # }
    #
    # # Define the headers with the API key
    # deepseek_headers = {
    #     "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    #
    # # Make the API request
    # response = requests.post(DEEPSEEK_API_URL, headers=deepseek_headers, json=payload)
    #
    # # Handle the response
    # if response.status_code == 200:
    #     response_data = response.json()
    #     summary = response_data["choices"][0]["message"]["content"].strip()
    #     print(summary)
    #     return summary
    # else:
    #     print(f"Error: {response.status_code}, {response.text}")
    #     return None

    prompt = f"""Given the following passenger details, generate a structured and concise summary.
    Format the summary professionally, including the title, full name, gender, email, phone number, date of birth,
    and age (calculated based on the current year). The output should be clear and readable.

    Passenger Data:
    {passenger_data}
    
    ✅  To confirm the booking please write 'Confirm my flight ticket'
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You generate structured passenger summaries in a professional format."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,  # Adjusted for complete output
        temperature=0.5
    )

    try:
        response_data = response.choices[0].message.content.strip()
        return response_data
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def main():
    # Initialize passenger data for 2 passengers (example: international flight)
    total_passengers = 4
    flight_type = "international"  # or "domestic"
    passenger_details = initialize_passenger_data(total_passengers, flight_type)
    passenger_memory.save_data(passenger_details)

    # Simulate user inputs
    inputs = [
        "My name is Mr Ibrahim khalil ibrahim@ibos.com 01515619886 A12345",
        "My name is Turin Tasmira",
        "Turin@akij.com 01750671424 A54321",
        "Ayesha Ibrat",
        "Ibrat@gmail.com",
        "01722744921 A543298",
        "Aaiza, Ibrat",
        "aaiza@gmail.com",
        "01722744921 A543298"
    ]

    passenger_index = 0
    for input_text in inputs:
        print(f"Processing input: {input_text}")
        details = extract_passenger_details(input_text)
        result = collect_passenger_details(passenger_index, flight_type, **details)
        print(result)

        # Move to the next passenger if all fields are filled
        if "Almost done" not in result:
            passenger_index += 1

    # Print final passenger data
    final_data = passenger_memory.load_data()
    print("Final Passenger Data:")
    print(final_data)

if __name__ == "__main__":
    main()