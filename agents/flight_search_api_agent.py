import json
import os
import openai
import requests
from tabulate import tabulate
from memory.json_memory import JSONMemory
from dotenv import load_dotenv
from datetime import datetime
from tools.utils import correct_airport_name


# Load environment variables
load_dotenv()
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}

client = openai.OpenAI(api_key=OPENAI_API_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def save_log_file(filename, content):
    with open(os.path.join(LOG_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)

FLIGHT_API_URL = os.getenv("FLIGHT_API_URL")
flight_memory = JSONMemory(os.path.join(DATA_DIR, "flight_search_data.json"))
flight_list_file = os.path.join(DATA_DIR, "flight_list.json")
passenger_memory = JSONMemory(os.path.join(DATA_DIR, "passenger_data.json"))

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "apikey": os.getenv("API_KEY"),
    "secretecode": os.getenv("SECRET_CODE")
}

from tools.utils import correct_airport_name  # <- Add this import assuming utils.py has the method

def get_airport_code(city):
    if not city:
        return None

    airports = {
        "Dhaka": {"Shahjalal International Airport": "DAC"},
        "Kathmandu": {"Tribhuvan International Airport": "KTM"},
        "Kolkata": {"Netaji Subhas Chandra Bose International Airport": "CCU"},
        "Chennai": {"Chennai International Airport": "MAA"},
        "Bangkok": {
            "Suvarnabhumi Airport": "BKK",
            "Don Mueang International Airport": "DMK"
        },
        "Phuket": {"Phuket International Airport": "HKT"},
        "Singapore": {"Singapore Changi Airport": "SIN"},
        "Kuala Lumpur": {"Kuala Lumpur International Airport": "KUL"},
        "Langkawi": {"Langkawi International Airport": "LGK"},
        "Dubai": {
            "Dubai International Airport": "DXB",
            "Al Maktoum International Airport": "DWC"
        },
        "London": {
            "Heathrow Airport": "LHR",
            "Gatwick Airport": "LGW",
            "London City Airport": "LCY",
            "Luton Airport": "LTN",
            "Stansted Airport": "STN"
        },
        "Manchester": {"Manchester Airport": "MAN"},
        "Tokyo (Narita)": {"Narita International Airport": "NRT"},
        "Doha": {"Hamad International Airport": "DOH"},
        "Maldives": {
            "Velana International Airport (Male)": "MLE",
            "Gan International Airport": "GAN"
        },
        "Muscat": {"Muscat International Airport": "MCT"},
        "Rome": {
            "Leonardo da Vinci–Fiumicino Airport": "FCO",
            "Ciampino–G. B. Pastine International Airport": "CIA"
        },
        "New York": {
            "John F. Kennedy International Airport": "JFK",
            "LaGuardia Airport": "LGA",
            "Newark Liberty International Airport": "EWR"
        },
        "Washington": {
            "Washington Dulles International Airport": "IAD",
            "Ronald Reagan Washington National Airport": "DCA",
            "Baltimore/Washington International Thurgood Marshall Airport": "BWI"
        },
        "Orlando, Florida": {
            "Orlando International Airport": "MCO",
            "Orlando Sanford International Airport": "SFB"
        },
        "Miami": {
            "Miami International Airport": "MIA",
            "Fort Lauderdale-Hollywood International Airport": "FLL"
        },
        "Bali": {"Ngurah Rai International Airport (Denpasar)": "DPS"},
        "Jakarta": {
            "Soekarno-Hatta International Airport": "CGK",
            "Halim Perdanakusuma International Airport": "HLP"
        },
        "Hanoi": {"Noi Bai International Airport": "HAN"},
        "Ho Chi Minh City": {"Tan Son Nhat International Airport": "SGN"},
        "Philippines": {
            "Ninoy Aquino International Airport (Manila)": "MNL",
            "Mactan-Cebu International Airport": "CEB",
            "Clark International Airport": "CRK"
        },
        "Guangzhou": {"Guangzhou Baiyun International Airport": "CAN"},
        "Kunming": {"Kunming Changshui International Airport": "KMG"},
        "Shanghai": {
            "Shanghai Pudong International Airport": "PVG",
            "Shanghai Hongqiao International Airport": "SHA"
        },
        "Chengdu": {
            "Chengdu Shuangliu International Airport": "CTU",
            "Chengdu Tianfu International Airport": "TFU"
        },
        "Hong Kong": {"Hong Kong International Airport": "HKG"},
        "Sydney": {"Sydney Kingsford Smith Airport": "SYD"},
        "Melbourne": {
            "Melbourne Airport (Tullamarine)": "MEL",
            "Avalon Airport": "AVV"
        },
        "Brisbane": {"Brisbane Airport": "BNE"},
        "Adelaide": {"Adelaide Airport": "ADL"},
        "Perth": {"Perth Airport": "PER"},
        "Wellington": {"Wellington International Airport": "WLG"},
        "Rio de Janeiro": {
            "Rio de Janeiro–Galeão International Airport": "GIG",
            "Santos Dumont Airport": "SDU"
        },
        "Buenos Aires": {
            "Ministro Pistarini International Airport (Ezeiza)": "EZE",
            "Jorge Newbery Airfield": "AEP"
        },
        "Mexico City": {"Mexico City International Airport": "MEX"},
        "Nairobi": {"Jomo Kenyatta International Airport": "NBO"},
        "Alexandria": {"Borg El Arab Airport": "HBE"},
        "Cairo": {"Cairo International Airport": "CAI"},
        "Moscow": {
            "Sheremetyevo International Airport": "SVO",
            "Domodedovo International Airport": "DME",
            "Vnukovo International Airport": "VKO"
        },
        "Tashkent": {"Tashkent International Airport": "TAS"},
        "Tbilisi": {"Tbilisi International Airport": "TBS"},
        "Ethiopia": {"Addis Ababa Bole International Airport": "ADD"},
        "Amsterdam": {"Amsterdam Airport Schiphol": "AMS"},
        "Paris": {
            "Charles de Gaulle Airport": "CDG",
            "Orly Airport": "ORY"
        },
        "Venice": {
            "Venice Marco Polo Airport": "VCE",
            "Treviso Airport": "TSF"
        },
        "Naples": {"Naples International Airport": "NAP"},
        "Barcelona": {"Barcelona–El Prat Airport": "BCN"},
        "Madrid": {"Adolfo Suárez Madrid–Barajas Airport": "MAD"},
        "Lisbon": {"Humberto Delgado Airport (Lisbon Airport)": "LIS"},
        "Malaga": {"Málaga-Costa del Sol Airport": "AGP"},
        "Toronto": {
            "Toronto Pearson International Airport": "YYZ",
            "Billy Bishop Toronto City Airport": "YTZ"
        },
        "Montreal": {"Montréal–Pierre Elliott Trudeau International Airport": "YUL"},
        "Zurich": {"Zurich Airport": "ZRH"},
        "Warsaw": {"Warsaw Chopin Airport": "WAW"},
        "Lagos": {"Murtala Muhammed International Airport": "LOS"},
        "Addis Ababa": {"Addis Ababa Bole International Airport": "ADD"},
        "Barishal": {"Barisal Airport": "BZL"},
        "Chittagong": {"Shah Amanat International Airport": "CGP"},
        "Saidpur": {"Saidpur Airport": "SPD"},
        "Rajshahi": {"Shah Makhdum Airport": "RJH"},
        "Sylhet": {"Osmani International Airport": "ZYL"},
        "Cox's Bazar": {"Cox's Bazar Airport": "CXB"},
        "Jessore": {"Jessore Airport": "JSR"}
    }

    city = city.lower().strip("()")  # Basic cleanup
    known_names = list(airports.keys())
    for airport_group in airports.values():
        known_names.extend(airport_group.keys())

    # 🧠 Use OpenAI to correct the airport/city name
    corrected = correct_airport_name(city, known_names)
    if not corrected:
        return None

    # ✅ Match the corrected result to known airports
    for loc, airport_group in airports.items():
        if corrected.lower() == loc.lower():
            return list(airport_group.values())[0]
        for name, code in airport_group.items():
            if corrected.lower() == name.lower():
                return code

    return None


# rest of the code remains as-is
airlines_dict = {
            "AA": "American Airlines",
            "AF": "Air France",
            "AI": "Air India",
            "AK": "AirAsia",
            "BA": "British Airways",
            "BG": "Biman Bangladesh Airlines",
            "BR": "EVA Air",
            "BS": "US-Bangla Airlines",
            "CA": "Air China",
            "CX": "Cathay Pacific",
            "DL": "Delta Air Lines",
            "EK": "Emirates",
            "ET": "Ethiopian Airlines",
            "EY": "Etihad Airways",
            "FR": "Ryanair",
            "IB": "Iberia",
            "JL": "Japan Airlines",
            "KE": "Korean Air",
            "KLM": "KLM Royal Dutch Airlines",
            "LH": "Lufthansa",
            "MH": "Malaysia Airlines",
            "QF": "Qantas",
            "QR": "Qatar Airways",
            "SQ": "Singapore Airlines",
            "TK": "Turkish Airlines",
            "UA": "United Airlines",
            "VS": "Virgin Atlantic",
            "WN": "Southwest Airlines"
        }

# Flight Search API Agent
def flight_search_api_agent():
    flight_details = flight_memory.load_data() or {}
    if not flight_details.get("origin") or not flight_details.get("destination"):
        return "❌ Missing flight details. Please provide origin and destination."

    payload = create_payload(flight_details)
    payload = payload.replace("None", "null")
    search_payload = json.loads(payload)
    save_log_file("flight_search_payload.json", json.dumps(search_payload, indent=4))

    response = requests.post("https://serviceapi.innotraveltech.com/flight/search",json=search_payload, headers=headers)
    print(f"Flight API Response Status Code: {response.status_code}")
    if response.status_code == 200:
        flights = response.json()
        save_log_file("flight_search_response.json", json.dumps(flights, indent=4))


        if "data" not in flights or not flights["data"]:
            print("❌ API response does not contain valid flight data!")
            return "❌ No flights available. Please try again later."

        with open(flight_list_file, "w") as f:
            json.dump(flights, f, indent=4)
            

        print("✅ Flight list successfully saved!")
        flight_list = _format_results(flights)
        return flight_list
    else:
        print(f"❌ Flight API Error: {response.status_code}, Response: {response.text}")
        error_content = f"Status Code: {response.status_code}\n\nResponse Text:\n{response.text}"
        save_log_file("flight_search_error.txt", error_content)
        return f"❌ Flight search failed. Error: {response.status_code}"
        

def _format_results(response_data):
    if "data" in response_data:
        data = response_data["data"]
        tracking_id = data[0].get("tracking_id", None)
        filtered_data = [
            {
                "carrier_operating": entry.get("filter", {}).get("carrier_operating", "N/A"),
                "airline_name": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("operating", {})
                    .get("carrier_name", "N/A")
                ),
                "origin_airport_short_name": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("origin", "N/A")
                ),
                "origin_airport_name": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("origin_airport", {})
                    .get("name", "N/A")
                ),
                "destination_airport_short_name": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("destination", "N/A")
                ),
                "destination_airport_name": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("destination_airport", {})
                    .get("name", "N/A")
                ),
                "flight_number": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("operating", {})
                    .get("flight_number", "N/A")
                ),
                "seat_available": (
                    entry.get("flight_group", [{}])[0]  # Access first element of list safely
                    .get("routes", [{}])[0]  # Access first route safely
                    .get("booking_class", {})
                    .get("seat_available", "N/A")
                ),
                "no_of_stops_title": (entry.get("flight_group", [{}])[0]).get("no_of_stops_title", "N/A"),
                "price": entry.get("filter", {}).get("price", "N/A"),
                "departure_departure_time": entry.get("filter", {}).get("departure_departure_time", "N/A"),
                "cabin_class": entry.get("filter", {}).get("cabin_class", "N/A"),
                "arrival_departure_time": entry.get("filter", {}).get("arrival_departure_time", "N/A"),
                "connecting_airport": entry.get("filter", {}).get("connecting_airport", "None"),

                "departure_date": extract_date_time(entry.get("filter", {}).get("departure_departure_time", "N/A"))[0],
                "departure_time": extract_date_time(entry.get("filter", {}).get("departure_departure_time", "N/A"))[1],
                "arrival_date": extract_date_time(entry.get("filter", {}).get("arrival_departure_time", "N/A"))[0],
                "arrival_time": extract_date_time(entry.get("filter", {}).get("arrival_departure_time", "N/A"))[1],

                "tracking_id": tracking_id,
                "id": entry.get("filter", {}).get("id", "N/A"),
            }
            for entry in data  # Ensure we loop over a list
        ]

        flight_list = clean_data(filtered_data)
        print(flight_list)
        return flight_list

    return "No data found in the response."

def generate_flight_table(flight_list):
    """Generates an HTML table from flight data with a 'Select Flight' button."""
    html_table = """
        <div class="flight-schedule-table">
        <table border="1" style="width:100%; border-collapse: collapse;">
            <thead>
                <tr class="flight-table-heading" style="background-color:#8E011A; color: white;">
                    <th>Airline</th>
                    <th>Price ($)</th>
                    <th>Departure Date</th>
                    <th>Departure Time</th>
                    <th>Cabin Class</th>
                    <th>Arrival Date</th>
                    <th>Arrival Time</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """

    for flight in flight_list:
        html_table += f"""
                <tr style="text-align:center;">
                    <td>{flight['carrier_operating']}</td>
                    <td>{flight['price']}</td>
                    <td>{flight['departure_date']}</td>
                    <td>{flight['departure_time']}</td>
                    <td>{flight['cabin_class']}</td>
                    <td>{flight['arrival_date']}</td>
                    <td>{flight['arrival_time']}</td>
                    <td>
                        <button class="flight_select-btn" onclick="selectFlight('{flight['tracking_id']}', '{flight['id']}')">
                            Select Flight
                        </button>
                    </td>
                </tr>
            """

    html_table += """
            </tbody>
        </table>
        </div>
        """

    return html_table


def clean_data(flights_data):
    for flight in flights_data:
        arrival_datetime = flight['arrival_departure_time']
        departure_datetime = flight['departure_departure_time']
        flight['arrival_date'], flight['arrival_time'] = arrival_datetime.split('T')[0], arrival_datetime.split('T')[1]
        flight['departure_date'], flight['departure_time'] = departure_datetime.split('T')[0], departure_datetime.split('T')[1]
        del flight['arrival_departure_time']
        del flight['departure_departure_time']
        flight['arrival_time'] = flight['arrival_time'][:-6]
        flight['departure_time'] = flight['departure_time'][:-6]
        if flight['carrier_operating'] in airlines_dict:
            flight['carrier_operating'] = airlines_dict[flight['carrier_operating']]
    return flights_data

def create_payload(flight_details):
    payload = {
        "journey_type": flight_details.get("journey_type", "OneWay"),
        "segment": [
            {
                "departure_airport_type": "AIRPORT",
                "departure_airport": get_airport_code(flight_details["origin"]),
                # Use IATA code if available
                "arrival_airport_type": "AIRPORT",
                "arrival_airport": get_airport_code(flight_details["destination"]),
                # Use IATA code if available
                "departure_date": flight_details["date_of_travel"],
            }
        ],
        "travelers_adult": flight_details.get("num_adults", 1),
        "travelers_child": flight_details.get("num_children", 0),
        "travelers_child_age": [],  # Can be populated if ages are collected
        "travelers_infants": 0,  # Defaulted to 0, can be updated dynamically
        "travelers_infants_age": [],  # Can be populated if ages are collected
        "fare_type": None,
        "fare_option": None,
        "content_type": None,
        "ptc_option": None,
        "agency_ethnic_list": None,
        "preferred_carrier": [],
        "non_stop_flight": "any",
        "baggage_option": "any",
        "booking_class": "Economy",
        "supplier_uid": "F1TT00041",  # Replace with actual supplier UID if dynamic
        "partner_id": "78",  # Replace with actual partner ID if dynamic
        "language": "en",
        "short_ref": "12121212121",  # Replace with a dynamic reference if needed
        "version": None,
    }

    if flight_details["journey_type"] == "RoundTrip" and flight_details["return_date"]:
        payload["segment"].append({
            "departure_airport": get_airport_code(flight_details["destination"]),
            "arrival_airport": get_airport_code(flight_details["origin"]),
            "departure_date": flight_details["return_date"],
        })
    else:
        payload["team_profile"] = [
            {
                "member_id": "1",
                "pax_type": "ADT"
            },
            {
                "member_id": "2",
                "pax_type": "CNN"
            },
            {
                "member_id": "3",
                "pax_type": "INF"
            }
        ]

    # print(f"payload: {json.dumps(payload)}")
    return json.dumps(payload)

def get_airport_code(city):
    airports = {
        "Dhaka": {"Shahjalal International Airport": "DAC"},
        "Kathmandu": {"Tribhuvan International Airport": "KTM"},
        "Kolkata": {"Netaji Subhas Chandra Bose International Airport": "CCU"},
        "Chennai": {"Chennai International Airport": "MAA"},
        "Bangkok": {
            "Suvarnabhumi Airport": "BKK",
            "Don Mueang International Airport": "DMK"
        },
        "Phuket": {"Phuket International Airport": "HKT"},
        "Singapore": {"Singapore Changi Airport": "SIN"},
        "Kuala Lumpur": {"Kuala Lumpur International Airport": "KUL"},
        "Langkawi": {"Langkawi International Airport": "LGK"},
        "Dubai": {
            "Dubai International Airport": "DXB",
            "Al Maktoum International Airport": "DWC"
        },
        "London": {
            "Heathrow Airport": "LHR",
            "Gatwick Airport": "LGW",
            "London City Airport": "LCY",
            "Luton Airport": "LTN",
            "Stansted Airport": "STN"
        },
        "Manchester": {"Manchester Airport": "MAN"},
        "Tokyo (Narita)": {"Narita International Airport": "NRT"},
        "Doha": {"Hamad International Airport": "DOH"},
        "Maldives": {
            "Velana International Airport (Male)": "MLE",
            "Gan International Airport": "GAN"
        },
        "Muscat": {"Muscat International Airport": "MCT"},
        "Rome": {
            "Leonardo da Vinci–Fiumicino Airport": "FCO",
            "Ciampino–G. B. Pastine International Airport": "CIA"
        },
        "New York": {
            "John F. Kennedy International Airport": "JFK",
            "LaGuardia Airport": "LGA",
            "Newark Liberty International Airport": "EWR"
        },
        "Washington": {
            "Washington Dulles International Airport": "IAD",
            "Ronald Reagan Washington National Airport": "DCA",
            "Baltimore/Washington International Thurgood Marshall Airport": "BWI"
        },
        "Orlando, Florida": {
            "Orlando International Airport": "MCO",
            "Orlando Sanford International Airport": "SFB"
        },
        "Miami": {
            "Miami International Airport": "MIA",
            "Fort Lauderdale-Hollywood International Airport": "FLL"
        },
        "Bali": {"Ngurah Rai International Airport (Denpasar)": "DPS"},
        "Jakarta": {
            "Soekarno-Hatta International Airport": "CGK",
            "Halim Perdanakusuma International Airport": "HLP"
        },
        "Hanoi": {"Noi Bai International Airport": "HAN"},
        "Ho Chi Minh City": {"Tan Son Nhat International Airport": "SGN"},
        "Philippines": {
            "Ninoy Aquino International Airport (Manila)": "MNL",
            "Mactan-Cebu International Airport": "CEB",
            "Clark International Airport": "CRK"
        },
        "Guangzhou": {"Guangzhou Baiyun International Airport": "CAN"},
        "Kunming": {"Kunming Changshui International Airport": "KMG"},
        "Shanghai": {
            "Shanghai Pudong International Airport": "PVG",
            "Shanghai Hongqiao International Airport": "SHA"
        },
        "Chengdu": {
            "Chengdu Shuangliu International Airport": "CTU",
            "Chengdu Tianfu International Airport": "TFU"
        },
        "Hong Kong": {"Hong Kong International Airport": "HKG"},
        "Sydney": {"Sydney Kingsford Smith Airport": "SYD"},
        "Melbourne": {
            "Melbourne Airport (Tullamarine)": "MEL",
            "Avalon Airport": "AVV"
        },
        "Brisbane": {"Brisbane Airport": "BNE"},
        "Adelaide": {"Adelaide Airport": "ADL"},
        "Perth": {"Perth Airport": "PER"},
        "Wellington": {"Wellington International Airport": "WLG"},
        "Rio de Janeiro": {
            "Rio de Janeiro–Galeão International Airport": "GIG",
            "Santos Dumont Airport": "SDU"
        },
        "Buenos Aires": {
            "Ministro Pistarini International Airport (Ezeiza)": "EZE",
            "Jorge Newbery Airfield": "AEP"
        },
        "Mexico City": {"Mexico City International Airport": "MEX"},
        "Nairobi": {"Jomo Kenyatta International Airport": "NBO"},
        "Alexandria": {"Borg El Arab Airport": "HBE"},
        "Cairo": {"Cairo International Airport": "CAI"},
        "Moscow": {
            "Sheremetyevo International Airport": "SVO",
            "Domodedovo International Airport": "DME",
            "Vnukovo International Airport": "VKO"
        },
        "Tashkent": {"Tashkent International Airport": "TAS"},
        "Tbilisi": {"Tbilisi International Airport": "TBS"},
        "Ethiopia": {"Addis Ababa Bole International Airport": "ADD"},
        "Amsterdam": {"Amsterdam Airport Schiphol": "AMS"},
        "Paris": {
            "Charles de Gaulle Airport": "CDG",
            "Orly Airport": "ORY"
        },
        "Venice": {
            "Venice Marco Polo Airport": "VCE",
            "Treviso Airport": "TSF"
        },
        "Naples": {"Naples International Airport": "NAP"},
        "Barcelona": {"Barcelona–El Prat Airport": "BCN"},
        "Madrid": {"Adolfo Suárez Madrid–Barajas Airport": "MAD"},
        "Lisbon": {"Humberto Delgado Airport (Lisbon Airport)": "LIS"},
        "Malaga": {"Málaga-Costa del Sol Airport": "AGP"},
        "Toronto": {
            "Toronto Pearson International Airport": "YYZ",
            "Billy Bishop Toronto City Airport": "YTZ"
        },
        "Montreal": {"Montréal–Pierre Elliott Trudeau International Airport": "YUL"},
        "Zurich": {"Zurich Airport": "ZRH"},
        "Warsaw": {"Warsaw Chopin Airport": "WAW"},
        "Lagos": {"Murtala Muhammed International Airport": "LOS"},
        "Addis Ababa": {"Addis Ababa Bole International Airport": "ADD"},
        "Barishal": {"Barisal Airport": "BZL"},
        "Chittagong": {"Shah Amanat International Airport": "CGP"},
        "Saidpur": {"Saidpur Airport": "SPD"},
        "Rajshahi": {"Shah Makhdum Airport": "RJH"},
        "Sylhet": {"Osmani International Airport": "ZYL"},
        "Cox's Bazar": {"Cox's Bazar Airport": "CXB"},
        "Jessore": {"Jessore Airport": "JSR"}
    }
    city = city.lower()  # Convert input city name to lowercase
    for location, airports in airports.items():
        if location.lower() == city:  # Compare in lowercase
            return list(airports.values())[0]  # Return the first airport code found
    return None

def extract_date_time(datetime_str):
    dt_obj = datetime.fromisoformat(datetime_str[:-6])  # Remove timezone offset
    date_part = dt_obj.date().strftime('%Y-%m-%d')
    time_part = dt_obj.time().strftime('%H:%M:%S')
    return date_part, time_part
