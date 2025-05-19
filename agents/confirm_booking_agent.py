import json
import os
import openai
import requests
from memory.json_memory import JSONMemory
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")  # Set the data folder inside the project

# Ensure the 'data' folder exists
os.makedirs(DATA_DIR, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}
# ✅ Define file paths
SELECTED_FLIGHT_FILE = os.path.join(DATA_DIR,"selected_flight.json")
PASSENGER_DATA_FILE = os.path.join(DATA_DIR,"passenger_data.json")

# # ✅ Load Passenger Data
# passenger_memory = JSONMemory(os.path.join(DATA_DIR, "passenger_data.json"))
# passenger_memory_info = passenger_memory.load_data() or {}
# passenger_data = passenger_memory_info.get("passengers", [])
#
# # ✅ Load Selected Flight Data
# selected_flight = JSONMemory(os.path.join(DATA_DIR, "selected_flight.json"))
# selected_flight_info = selected_flight.load_data() or {}
# booking_tracking_id = selected_flight_info.get("booking_tracking_id", "UNKNOWN_TRACKING_ID")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "apikey": os.getenv("API_KEY"),
    "secretecode": os.getenv("SECRET_CODE")
}

# if passenger_memory_info:
#     first_passenger_data = passenger_memory_info.get("passengers", [])[0]
#     name = first_passenger_data.get("first_name", "") + " "+first_passenger_data.get("last_name", "")
#     email = first_passenger_data.get("email", "UNKNOWN_EMAIL")
#     contact = first_passenger_data.get("phone", "UNKNOWN_Contact")
# else:
#     name = "UNKNOWN"
#     email = "UNKNOWN"
#     contact = "UNKNOWN"


def confirm_booking_agent():
    # ✅ Load Passenger Data
    passenger_memory = JSONMemory(os.path.join(DATA_DIR, "passenger_data.json"))
    passenger_memory_info = passenger_memory.load_data() or {}
    passenger_data = passenger_memory_info.get("passengers", [])

    # ✅ Load Selected Flight Data
    selected_flight = JSONMemory(os.path.join(DATA_DIR, "selected_flight.json"))
    selected_flight_info = selected_flight.load_data() or {}
    booking_tracking_id = selected_flight_info.get("booking_tracking_id", "UNKNOWN_TRACKING_ID")

    if passenger_memory_info:
        first_passenger_data = passenger_memory_info.get("passengers", [])[0]
        name = first_passenger_data.get("first_name", "") + " " + first_passenger_data.get("last_name", "")
        email = first_passenger_data.get("email", "UNKNOWN_EMAIL")
        contact = first_passenger_data.get("phone", "UNKNOWN_Contact")
    else:
        name = "UNKNOWN"
        email = "UNKNOWN"
        contact = "UNKNOWN"


    passenger_details_payload = get_passenger_details_payload(passenger_data, booking_tracking_id, selected_flight_info)
    update_travelers_response = update_travelers(passenger_details_payload)
    if update_travelers_response:
        return update_travelers_response  # Return error message if traveler update fails
    print("Step 2: Creating booking...")
    booking_data = create_booking(passenger_details_payload, booking_tracking_id, email, contact)
    if isinstance(booking_data, str):  # If an error message is returned
        return booking_data
    print("Step 3: Fetching booking details...")
    booking_details = fetch_booking_details(booking_tracking_id)

    response = initiate_payment_request(passenger_details_payload, booking_details, booking_tracking_id, name, email, contact)
    return response

def calculate_pax_type(dob):
    """Determine passenger type based on date of birth."""
    from datetime import datetime

    try:
        birth_year = int(dob.split("-")[0])
        current_year = datetime.now().year
        age = current_year - birth_year

        if age < 2:
            return "INF"  # Infant
        elif age < 12:
            return "CHD"  # Child
        else:
            return "ADT"  # Adult
    except ValueError:
        return "ADT"  # Default to adult if DOB is invalid

def get_passenger_details_payload(passenger_data, booking_tracking_id, selected_flight_info):
    """
    Generates a structured payload for booking confirmation,
    including flight and passenger details.
    """
    # ✅ Default document details
    default_data = {
        "doc_country": "BD",
        "doc_no": "A1235121",
        "doc_dateofexpiry": "2030-04-25",
        "doc_dateofissue": "",
        "passport_copy": "https://itt-documents-copy.s3.amazonaws.com/passport-copy/default-passport.jpeg"
    }
    passenger_details_payload = []
    # ✅ Assign pax_id starting from 1
    for index, passenger in enumerate(passenger_data, start=1):
        pax_type = calculate_pax_type(passenger.get("dob", "1990-01-01"))

        # ✅ Extract document details if available
        doc_no = passenger.get("passport_number", default_data["doc_no"])
        doc_dateofexpiry = passenger.get("date_of_expiry", default_data["doc_dateofexpiry"])
        doc_dateofissue = passenger.get("date_of_issue", default_data["doc_dateofissue"])
        passport_copy = passenger.get("passport_copy", default_data["passport_copy"])

        # ✅ Build passenger structure
        complete_passenger_data = {
            "pax_id": index,  # ✅ pax_id now starts from 1 and increments
            "pax_type": pax_type,
            "title": passenger.get("title", "N/A"),
            "gender": passenger.get("gender", "N/A"),
            "first_name": passenger.get("first_name", "N/A"),
            "last_name": passenger.get("last_name", "N/A"),
            "email": passenger.get("email", "N/A"),
            "contact_number": passenger.get("phone", "N/A"),
            "dob": passenger.get("dob", "1990-01-01"),
            "doc_country": default_data["doc_country"],
            "doc_no": doc_no,
            "doc_dateofexpiry": doc_dateofexpiry,
            "doc_dateofissue": doc_dateofissue,
            "passport_copy": passport_copy
        }

        passenger_details_payload.append(complete_passenger_data)

    # ✅ Build Final Booking Payload
    final_payload = {
        "booking_tracking_id": booking_tracking_id,
        "member_id": "2",
        "save_pax": "yes",
        "flight_details": selected_flight_info,  # ✅ FIXED: Use Dictionary Instead of JSONMemory Object
        "passenger": passenger_details_payload
    }
    return final_payload

def update_travelers(passenger_details_payload):
    print("Step 1: Updating traveler information...")
    url = "https://serviceapi.innotraveltech.com/flight/update-travellers"
    try:
        response = requests.post(url, headers=headers, json=passenger_details_payload)
        print(f"Update Travelers API Response: {response.status_code}, {response.text}")
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            return data.get("reason", "An unknown error occurred while updating travelers.")

        print("Traveler information updated successfully.")
        return None
    except Exception as e:
        print(f"Error during traveler update: {e}")
        return "An error occurred while updating travelers. Please try again."

def create_booking(passenger_details_payload, booking_tracking_id, email, contact):
    print("Step 2: Creating booking...")
    create_booking_url = "https://serviceapi.innotraveltech.com/flight/create-booking"
    payload = {
        "booking_tracking_id": booking_tracking_id,
        "member_id": passenger_details_payload.get("member_id", "2"),
        "isd_code": "880",
        "contact_no": contact,
        "email_address": email,
        "payment_type": "onlinepayment",
        "isPartialPay": "yes",
        "redirect_url": "https://showkat.innovatedemo.com/inno-travel-tech/custom_modal.html"
    }

    try:
        response = requests.post(create_booking_url, headers=headers, json=payload)
        response.raise_for_status()
        booking_data = response.json()
        if booking_data.get("status") != "success":
            return booking_data.get("reason", "An unknown error occurred while creating booking.")

        print("Booking created successfully.")
        return booking_data
    except requests.exceptions.RequestException as e:
        print(f"Create Booking API Error: {e}")
        return "An error occurred while creating booking. Please try again."

def fetch_booking_details(booking_tracking_id):
    """
    Step 3: Fetch booking details.
    """
    # booking_id = booking_data.get("booking_id", "")
    booking_details = {}
    print(booking_tracking_id)
    booking_details_url = "https://serviceapi.innotraveltech.com/flight/booking-details"
    payload = {
        "tracking_id": booking_tracking_id,
        "booking_id": "",
        "member_id": "1"
    }

    try:
        response = requests.post(booking_details_url, headers=headers, json=payload)
        response.raise_for_status()
        booking_details = response.json()
        if response.status_code != 200:
            raise Exception("Failed to fetch booking details.")
        if booking_details.get("status") != "success":
            return booking_details.get("reason", "Failed to fetch booking details.")

        print("Booking details fetched successfully.")
        return booking_details
    except requests.exceptions.RequestException as e:
        print(f"Fetch Booking Details API Error: {e}")
        return "An error occurred while fetching booking details."

def initiate_payment_request(passenger_details_payload, booking_details, booking_tracking_id, name, email, contact):
    print("Step 4: Initiating payment request...")
    payment_request_url = "https://checkout.innotraveltech.com/request"
    payload = {
        "ftm_partner_id": "1",
        "member_id": "1",
        "tracking_id": booking_tracking_id,
        "collection_type": "payment_link",
        "payment_link_valid": "2030-10-12 23:10",
        "payment_link_base_url": "https://agent.inno.com/online-payment",
        "currency": "USD",
        "amount": "1",
        "redirect_url": "https://showkat.innovatedemo.com/inno-travel-tech/custom_modal.html",
        "email": email,
        "name": name,
        "isd_code": "880",
        "contact_number": contact,
        "service_details": "Flight booking confirmation and payment",
        "booking_data": {}
    }

    print(f"Payment Request Payload: {payload}")

    try:
        response = requests.post(payment_request_url, headers=headers, json=payload)
        print(f"Payment Request Response: {response.status_code}, {response.text}")
        response.raise_for_status()

        payment_data = response.json()
        if payment_data.get("status") != "success":
            raise Exception(f"Payment request failed: {payment_data.get('message', 'Unknown error')}")

        payment_link = payment_data.get("payment_link")
        ## Step 5: Generate Confirmation Message via OpenAI
        extracted_info = generate_booking_confirmation_message(passenger_details_payload, booking_details, payment_link)
        return extracted_info
    except requests.exceptions.RequestException as e:
        raise Exception(f"Payment Request API Error: {e}")

def generate_booking_confirmation_message(passenger_details_payload, booking_details, payment_link):
    """
    Generates a professional flight booking confirmation message using OpenAI API.

    Parameters:
        passenger_details_payload (dict): Passenger details in JSON format.
        booking_details (dict): Flight booking details.
        payment_link (str): Link to complete the payment.

    Returns:
        str: A structured, friendly, and clear booking confirmation message.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    # ✅ System message for context
    system_message = """
    You are a professional and friendly flight booking assistant. A flight reservation has been successfully completed,
    and you have received the booking details in JSON format.

    Your task is to generate a warm, clear, and reassuring confirmation message using the provided JSON data.
    The message should summarize the key flight booking details for the user.

    The message must include:
    - A friendly acknowledgment of the successful booking.
    - Key booking details such as airline, flight number, departure and arrival cities, dates, and total price.
    - Assurance that the booking is secure and confirmed.
    - A polite invitation to contact support if needed.

    Ensure the message is concise, professional, and easy to read. Avoid unnecessary complexity.
    """

    # ✅ User Prompt with Booking Details
    user_prompt = f"""
    Generate a professional, clear, and engaging **flight booking confirmation message** using the following data:

    📌 **Passenger Information**
    Each passenger includes the following details:
    - **Title:** (e.g., Mr./Ms./Dr.)
    - **Gender:** (Male/Female/Other)
    - **First Name** and **Last Name**
    - **Email Address**
    - **Contact Number**
    - **Date of Birth**

    👤 **Passenger Data:**
    ```json
    {passenger_details_payload}
    ```

    📋 **Booking Details**
    - **📌 Booking Reference**
    - **✈️ Flight Number**
    - **🛫 Departure Time**
    - **🛬 Arrival Time**
    - **🌍 Departure City**
    - **🌍 Arrival City**

    📜 **Booking Information:**
    ```json
    {booking_details}
    ```

    💳 **Payment Information**
    👉 [Complete Your Payment Here]({payment_link})

    📢 **Instructions for the Confirmation Message:**
    - Clearly list **all passenger details** (Title, Gender, Full Name, Email, Contact Number, and Date of Birth).
    - Highlight **Booking Reference, Flight Details, and Payment Link** prominently.
    - Use **icons** (✈️ for flights, 💳 for payment) to enhance readability.
    - Structure the message for **clarity and visual appeal**.
    - Express **gratitude** for booking with **AKIJ AIR**.
    - Make the message **engaging, warm, and professional**.

    ✅ **Does this look correct?** Let me know if you need any changes!
    Please respond with **'yes'** to proceed or **'no'** to modify anything.

    **Best regards,**
    ✈️ **AKIJ AIR** 🛫
    """

    # ✅ Generate response using OpenAI's latest API format
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
        )

        # ✅ Extract response content
        confirmation_message = response.choices[0].message.content.strip()
        print("✅ Booking Confirmation Generated!")
        print(confirmation_message)
        return confirmation_message

    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return "An error occurred while generating the confirmation message. Please try again."

# def generate_booking_confirmation_message(passenger_details_payload, booking_details, payment_link):
#     """
#     Generates a professional flight booking confirmation message using OpenAI API.
#
#     Parameters:
#         passenger_details_payload (dict): Passenger details in JSON format.
#         booking_details (dict): Flight booking details.
#         payment_link (str): Link to complete the payment.
#
#     Returns:
#         str: A structured, friendly, and clear booking confirmation message.
#     """
#     # System message for context
#     system_message = """
#             You are a professional and friendly flight booking assistant. A flight reservation has been successfully completed,
#             and you have received the booking details in JSON format.
#
#             Your task is to generate a warm, clear, and reassuring confirmation message using the provided JSON data.
#             The message should summarize the key flight booking details for the user.
#
#             The message must include:
#             - A friendly acknowledgment of the successful booking.
#             - Key booking details such as airline, flight number, departure and arrival cities, dates, and total price.
#             - Assurance that the booking is secure and confirmed.
#             - A polite invitation to contact support if needed.
#
#             Ensure the message is concise, professional, and easy to read. Avoid unnecessary complexity.
#             """
#
#     # ✅ User Prompt with Booking Details
#     user_prompt = f"""
#     Generate a professional, clear, and engaging **flight booking confirmation message** using the following data:
#
#     📌 **Passenger Information**
#     Each passenger includes the following details:
#     - **Title:** (e.g., Mr./Ms./Dr.)
#     - **Gender:** (Male/Female/Other)
#     - **First Name** and **Last Name**
#     - **Email Address**
#     - **Contact Number**
#     - **Date of Birth**
#
#     👤 **Passenger Data:**
#     ```json
#     {passenger_details_payload}
#     ```
#
#     📋 **Booking Details**
#     - **📌 Booking Reference**
#     - **✈️ Flight Number**
#     - **🛫 Departure Time**
#     - **🛬 Arrival Time**
#     - **🌍 Departure City**
#     - **🌍 Arrival City**
#
#     📜 **Booking Information:**
#     ```json
#     {booking_details}
#     ```
#
#     💳 **Payment Information**
#     👉 [Complete Your Payment Here]({payment_link})
#
#     📢 **Instructions for the Confirmation Message:**
#     - Clearly list **all passenger details** (Title, Gender, Full Name, Email, Contact Number, and Date of Birth).
#     - Highlight **Booking Reference, Flight Details, and Payment Link** prominently.
#     - Use **icons** (✈️ for flights, 💳 for payment) to enhance readability.
#     - Structure the message for **clarity and visual appeal**.
#     - Express **gratitude** for booking with **AKIJ AIR**.
#     - Make the message **engaging, warm, and professional**.
#
#     **Best regards,**
#     ✈️ **AKIJ AIR** 🛫
#     """
#     payload = {
#         "model": "deepseek-model-name",  # Replace with the actual model name
#         "messages": [
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": user_prompt}
#         ],
#         "max_tokens": 300,  # Adjusted for a detailed response
#         "temperature": 0.5  # Balanced creativity and focus
#     }
#     # ✅ Generate response using OpenAI's latest API format
#     try:
#         response = requests.post(DEEPSEEK_API_URL, headers=deepseek_headers, json=payload)
#         if response.status_code == 200:
#             response_data = response.json()
#             confirmation_message = response_data["choices"][0]["message"]["content"].strip()
#             print("✅ Booking Confirmation Generated!")
#             print(confirmation_message)
#             return confirmation_message
#         else:
#             print(f"❌ DeepSeek API Error: {response.status_code}, {response.text}")
#             return f"❌ DeepSeek API Error: {response.status_code}, {response.text}"
#     except Exception as e:
#         print(f"❌ OpenAI API Error: {e}")
#         return "An error occurred while generating the confirmation message. Please try again."
