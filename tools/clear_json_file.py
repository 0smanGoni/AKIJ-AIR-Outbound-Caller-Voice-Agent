import json
import os
from agents.agent_selector import select_agent

# ✅ Get absolute path to ensure compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")  # Data directory inside the project

# ✅ Define file paths correctly within the project
json_files = [
    os.path.join(DATA_DIR, "pending_flight_data.json"),
    os.path.join(DATA_DIR, "pending_passenger_data.json"),
    os.path.join(DATA_DIR, "flight_search_data.json"),
    os.path.join(DATA_DIR, "passenger_data.json"),
    os.path.join(DATA_DIR, "flight_list.json"),
    os.path.join(DATA_DIR, "user_location_data.json")
]

def clear_json_files():
    """Clears all stored JSON files by overwriting them with appropriate empty structures."""
    # ✅ Ensure the `data/` directory exists before writing files
    os.makedirs(DATA_DIR, exist_ok=True)

    for file in json_files:
        try:
            # ✅ Determine whether the file stores an object `{}` or a list `[]`
            empty_data = {} if "passenger_data.json" in file or "flight_search_data.json" in file else []

            # ✅ Overwrite file with an empty JSON structure
            with open(file, "w", encoding="utf-8") as f:
                json.dump(empty_data, f, indent=4)

            print(f"✅ Cleared file: {file}")

        except Exception as e:
            print(f"❌ Error clearing {file}: {e}")

# ✅ Clear JSON files before the app starts
clear_json_files()
