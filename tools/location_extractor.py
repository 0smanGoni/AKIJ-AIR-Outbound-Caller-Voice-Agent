import json
import re
from typing import Optional

from langchain_openai import ChatOpenAI
import spacy
from dateutil import parser
import os
from dotenv import load_dotenv
import openai
# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ✅ Load NLP Model (Ensure `en_core_web_sm` is installed)
nlp = spacy.load("en_core_web_sm")

# ✅ Initialize GPT-4
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)


def extract_location(text, keyword=None):
    """
    Uses GPT-4 to directly extract 'origin' and 'destination' first.
    If GPT fails, falls back to NLP (spaCy) for location extraction.
    """
    # print(f"\n🧠 [Before GPT-4] Raw User Input: {text}")

    # ✅ Step 1: Ask GPT-4 to extract structured location details
    gpt_locations = extract_locations_with_gpt(text)

    if gpt_locations:
        # print(f"🌍 [From GPT] Extracted Locations: {gpt_locations}")
        if keyword == "from":
            return gpt_locations.get("origin")
        elif keyword == "to":
            return gpt_locations.get("destination")

    # print("❌ GPT-4 Failed to Extract Locations. Falling back to NLP.")

    # ✅ Step 2: Use NLP if GPT fails
    return extract_location_with_nlp(text, keyword)


def extract_locations_with_gpt(text):
    """
    Uses GPT-4 to extract origin and destination locations in structured JSON format.
    Example: "I want to go to Madrid from Dhaka" → {"origin": "Dhaka", "destination": "Madrid"}
    """

    prompt = f"""
    You are a travel assistant. Extract the **origin** and **destination** from the following text.

    **User Input:** "{text}"

    Respond in this exact JSON format:
    {{
        "origin": "<extracted_origin>",
        "destination": "<extracted_destination>"
    }}

    If a location is missing, return `"null"` for that field.
    """

    try:
        client = openai.Client()  # ✅ Initialize OpenAI client
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.3,
        )

        response_text = response.choices[0].message.content.strip()

        # ✅ Convert JSON response into a dictionary
        gpt_locations = eval(response_text)

        return gpt_locations if isinstance(gpt_locations, dict) else None

    except Exception as e:
        print(f"❌ GPT-4 Extraction Failed: {e}")
        return None  # Fail-safe fallback


def extract_location_with_nlp(text, keyword=None):
    """
    Extracts a city name using NLP (Named Entity Recognition) if GPT fails.
    """

    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]

    origin, destination = None, None

    # ✅ Improved regex for better extraction
    from_match = re.search(r"\bfrom\s+([\w\s]+?)(?=\s|$)", text, re.IGNORECASE)
    to_match = re.search(r"\bto\s+([\w\s]+?)(?=\s|$)", text, re.IGNORECASE)

    if keyword == "from":
        if from_match:
            return from_match.group(1).strip()
        elif len(locations) > 0:
            return " ".join(locations[0].split())  # ✅ Ensure multi-word cities are captured correctly

    if keyword == "to":
        if to_match:
            return to_match.group(1).strip()
        elif len(locations) > 1:
            return " ".join(locations[1].split())  # ✅ Handle multi-word cities

    return None

def extract_date(text):
    """
    Extracts a travel date from text.
    """
    try:
        parsed_date = parser.parse(text, fuzzy=True)
        return parsed_date.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def extract_return_date(text: str) -> Optional[str]:
    """
    Extracts the return date from the user input.
    """
    # Look for phrases like "return on", "coming back on", or "back on"
    return_date_match = re.search(r"(?:return on|coming back on|back on)\s+(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if return_date_match:
        return return_date_match.group(1)
    return None
def extract_number(text, keyword=None):
    """
    Extracts a number associated with a keyword (e.g., "adults" or "children") from the text.
    Supports both digits (2, 3) and word-based numbers ("two", "three").
    """
    word_to_number = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, 'None': 0
    }

    text = text.lower()  # Convert text to lowercase

    # ✅ Check if the text contains a word-based number and replace it
    for word, num in word_to_number.items():
        text = text.replace(f" {word} ", f" {num} ")

    # ✅ Extract number before a keyword (if specified)
    if keyword:
        match = re.search(r'(\d+)\s+' + re.escape(keyword), text)
        return int(match.group(1)) if match else 0

    # ✅ Extract first number found in text
    match = re.search(r'\b\d+\b', text)
    return int(match.group()) if match else 0