import json
import datetime
import os
import openai
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()


# Disable LangSmith API warnings
os.environ["LANGCHAIN_TRACING_V2"] = "false"

FLIGHT_SEARCH_FILE = "data/flight_search_data.json"
PASSENGER_DETAILS_FILE = "data/passenger_data.json"



def correct_airport_name(input_text, known_names):
    import openai
    prompt = f"""
    Match the following name to the closest valid option from the list below:
    List: {known_names}

    Input: {input_text}
    Output: Best matching valid name.
    """

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0
    )
    return response.choices[0].message.content.strip()


def load_data(file):
    """Loads JSON data from a file."""
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(file, new_data, update_last_entry=False):
    """
    Saves data to a JSON file.
    - `update_last_entry=True`: Updates the last entry instead of appending.
    - `update_last_entry=False`: Appends new data.
    """
    existing_data = load_data(file)

    if update_last_entry and existing_data:
        existing_data[-1].update(new_data)  # ✅ Update last entry
    else:
        existing_data.append(new_data)  # ✅ Append new entry

    with open(file, "w") as f:
        json.dump(existing_data, f, indent=4)

def get_current_time():
    """Returns the current time in H:MM AM/PM format."""
    return datetime.datetime.now().strftime("%I:%M %p")

# ✅ Define Schema for StructuredTool
class TimeInputSchema(BaseModel):
    pass
