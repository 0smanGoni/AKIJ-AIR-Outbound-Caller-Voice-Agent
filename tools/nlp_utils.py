import re
import openai
import spacy
from config import OPENAI_API_KEY

# Load NLP model (English)
nlp = spacy.load("en_core_web_sm")

class NLPUtils:
    """Extracts locations using GPT-4 or NLP if GPT fails."""

    def __init__(self):
        self.client = openai.Client(api_key=OPENAI_API_KEY)

    def extract_locations_with_gpt(self, text):
        """Extracts origin & destination using GPT-4."""
        prompt = f"""
        You are a travel assistant. Extract the **origin** and **destination** from the following text.

        **User Input:** "{text}"

        Respond in this exact JSON format:
        {{
            "origin": "<extracted_origin>",
            "destination": "<extracted_destination>"
        }}

        If a location is missing, return "null" for that field.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful travel assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )
            return eval(response.choices[0].message.content.strip())

        except Exception as e:
            print(f"❌ GPT-4 Extraction Failed: {e}")
            return None

    def extract_location_with_nlp(self, text, keyword=None):
        """Extracts a city name using NLP if GPT fails."""
        doc = nlp(text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]

        from_match = re.search(r"\bfrom\s+([\w\s]+?)(?=\s|$)", text, re.IGNORECASE)
        to_match = re.search(r"\bto\s+([\w\s]+?)(?=\s|$)", text, re.IGNORECASE)

        if keyword == "from" and from_match:
            return from_match.group(1).strip()
        elif keyword == "to" and to_match:
            return to_match.group(1).strip()

        return locations[0] if locations else None
