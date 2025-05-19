import json

import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from memory.json_memory import JSONMemory
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")
USER_LOCATION_DATA_FILE = os.path.join(DATA_DIR, "user_location_data.json")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)  # OpenAI LLM for validation

def get_country_from_text(location_text):
    """
    Converts a text-based location (e.g., 'Dhaka, Bangladesh') to a country name.
    Uses OpenAI for validation if needed.
    """
    try:
        prompt = f"Extract the country name from the following location text: '{location_text}'. Return only the country name."
        response = llm.invoke([HumanMessage(content=prompt)])
        country_name = response.content.strip()
        return country_name if country_name else "Unknown"
    except Exception as e:
        return f"Error detecting country: {e}"

def get_language_by_country(country_name):
    """
    Maps country names to their most commonly spoken language.
    """
    country_language_map = {
        "Afghanistan": "Pashto, Dari",
        "Albania": "Albanian",
        "Algeria": "Arabic",
        "Andorra": "Catalan",
        "Angola": "Portuguese",
        "Argentina": "Spanish",
        "Armenia": "Armenian",
        "Australia": "English",
        "Austria": "German",
        "Azerbaijan": "Azerbaijani",
        "Bahamas": "English",
        "Bahrain": "Arabic",
        "Bangladesh": "Bengali",
        "Barbados": "English",
        "Belarus": "Belarusian, Russian",
        "Belgium": "Dutch, French, German",
        "Belize": "English",
        "Benin": "French",
        "Bhutan": "Dzongkha",
        "Bolivia": "Spanish, Quechua, Aymara",
        "Bosnia and Herzegovina": "Bosnian, Croatian, Serbian",
        "Botswana": "English, Tswana",
        "Brazil": "Portuguese",
        "Brunei": "Malay",
        "Bulgaria": "Bulgarian",
        "Burkina Faso": "French",
        "Burundi": "Kirundi, French",
        "Cambodia": "Khmer",
        "Cameroon": "French, English",
        "Canada": "English, French",
        "Cape Verde": "Portuguese",
        "Central African Republic": "French, Sango",
        "Chad": "French, Arabic",
        "Chile": "Spanish",
        "China": "Mandarin",
        "Colombia": "Spanish",
        "Comoros": "Comorian, Arabic, French",
        "Congo (Democratic Republic)": "French, Lingala, Swahili",
        "Costa Rica": "Spanish",
        "Croatia": "Croatian",
        "Cuba": "Spanish",
        "Cyprus": "Greek, Turkish",
        "Czech Republic": "Czech",
        "Denmark": "Danish",
        "Djibouti": "French, Arabic",
        "Dominican Republic": "Spanish",
        "Ecuador": "Spanish",
        "Egypt": "Arabic",
        "El Salvador": "Spanish",
        "Equatorial Guinea": "Spanish, French, Portuguese",
        "Eritrea": "Tigrinya, Arabic, English",
        "Estonia": "Estonian",
        "Eswatini": "Swazi, English",
        "Ethiopia": "Amharic",
        "Fiji": "English, Fijian, Hindi",
        "Finland": "Finnish, Swedish",
        "France": "French",
        "Gabon": "French",
        "Gambia": "English",
        "Georgia": "Georgian",
        "Germany": "German",
        "Ghana": "English",
        "Greece": "Greek",
        "Guatemala": "Spanish",
        "Guinea": "French",
        "Guinea-Bissau": "Portuguese",
        "Guyana": "English",
        "Haiti": "Haitian Creole, French",
        "Honduras": "Spanish",
        "Hungary": "Hungarian",
        "Iceland": "Icelandic",
        "India": "Hindi, English",
        "Indonesia": "Indonesian",
        "Iran": "Persian",
        "Iraq": "Arabic, Kurdish",
        "Ireland": "English, Irish",
        "Israel": "Hebrew",
        "Italy": "Italian",
        "Ivory Coast": "French",
        "Jamaica": "English",
        "Japan": "Japanese",
        "Jordan": "Arabic",
        "Kazakhstan": "Kazakh, Russian",
        "Kenya": "English, Swahili",
        "Kuwait": "Arabic",
        "Kyrgyzstan": "Kyrgyz, Russian",
        "Laos": "Lao",
        "Latvia": "Latvian",
        "Lebanon": "Arabic",
        "Lesotho": "Sesotho, English",
        "Liberia": "English",
        "Libya": "Arabic",
        "Liechtenstein": "German",
        "Lithuania": "Lithuanian",
        "Luxembourg": "Luxembourgish, French, German",
        "Madagascar": "Malagasy, French",
        "Malawi": "English, Chichewa",
        "Malaysia": "Malay",
        "Maldives": "Dhivehi",
        "Mali": "French",
        "Malta": "Maltese, English",
        "Mauritania": "Arabic",
        "Mauritius": "English, French",
        "Mexico": "Spanish",
        "Moldova": "Romanian",
        "Monaco": "French",
        "Mongolia": "Mongolian",
        "Montenegro": "Montenegrin",
        "Morocco": "Arabic, Berber",
        "Mozambique": "Portuguese",
        "Myanmar": "Burmese",
        "Namibia": "English",
        "Nepal": "Nepali",
        "Netherlands": "Dutch",
        "New Zealand": "English, Maori",
        "Nicaragua": "Spanish",
        "Niger": "French",
        "Nigeria": "English",
        "North Korea": "Korean",
        "North Macedonia": "Macedonian",
        "Norway": "Norwegian",
        "Oman": "Arabic",
        "Pakistan": "Urdu, English",
        "Palestine": "Arabic",
        "Panama": "Spanish",
        "Papua New Guinea": "English, Tok Pisin",
        "Paraguay": "Spanish, Guarani",
        "Peru": "Spanish",
        "Philippines": "Filipino, English",
        "Poland": "Polish",
        "Portugal": "Portuguese",
        "Qatar": "Arabic",
        "Romania": "Romanian",
        "Russia": "Russian",
        "Rwanda": "Kinyarwanda, French, English",
        "Saudi Arabia": "Arabic",
        "Senegal": "French",
        "Serbia": "Serbian",
        "Sierra Leone": "English",
        "Singapore": "English, Malay, Mandarin, Tamil",
        "Slovakia": "Slovak",
        "Slovenia": "Slovene",
        "Solomon Islands": "English",
        "Somalia": "Somali, Arabic",
        "South Africa": "Afrikaans, English, Zulu, Xhosa",
        "South Korea": "Korean",
        "South Sudan": "English",
        "Spain": "Spanish",
        "Sri Lanka": "Sinhala, Tamil",
        "Sudan": "Arabic, English",
        "Sweden": "Swedish",
        "Switzerland": "German, French, Italian",
        "Syria": "Arabic",
        "Taiwan": "Mandarin",
        "Tajikistan": "Tajik",
        "Tanzania": "Swahili, English",
        "Thailand": "Thai",
        "Togo": "French",
        "Tunisia": "Arabic",
        "Turkey": "Turkish",
        "Turkmenistan": "Turkmen",
        "Uganda": "English, Swahili",
        "Ukraine": "Ukrainian",
        "United Arab Emirates": "Arabic",
        "United Kingdom": "English",
        "United States": "English",
        "Uruguay": "Spanish",
        "Uzbekistan": "Uzbek",
        "Venezuela": "Spanish",
        "Vietnam": "Vietnamese",
        "Yemen": "Arabic",
        "Zambia": "English",
        "Zimbabwe": "English, Shona, Ndebele"
    }

    return country_language_map.get(country_name, "Unknown")

def detect_language_from_text(location_text):
    """
    Detects the most spoken language based on user's text location.
    """
    country = get_country_from_text(location_text)
    if country == "Unknown":
        return "❌ Unable to determine location from text."

    language = get_language_by_country(country)
    if language == "Unknown":
        return f"🌍 Location detected: {country}, but language not found."

    os.makedirs(os.path.dirname(USER_LOCATION_DATA_FILE), exist_ok=True)
    user_location_language = {
        "country": country,
        "language": language,
    }
    print(user_location_language)

    try:
        # ✅ Save new flight data, overwriting previous data
        with open(USER_LOCATION_DATA_FILE, "w") as f:
            json.dump(user_location_language, f, indent=4)

        print("✅ User Location and Language saved!")

    except Exception as e:
        print(f"❌ Error saving flight data: {e}")

    return language

# ✅ Example Usage
if __name__ == "__main__":
    location_text = "Brazil"  # Example text-based location input
    detected_language = detect_language_from_text(location_text)
    print(detected_language)
