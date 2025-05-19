import os
import json
import chromadb
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings
# from db_driver import DatabaseDriver, PassengerDetails  # Import DB Driver
# from vector_db import store_in_vector_db  # Import VectorDB Storage

# ✅ Define Paths for JSON Memory & ChromaDB Storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves one level up
DATA_DIR = os.path.join(BASE_DIR, "data")  # Ensure JSON memory & ChromaDB store here
CHROMA_DB_PATH = os.path.join(DATA_DIR, "chromadb_store")  # Store ChromaDB inside "data"

# ✅ Ensure 'data' directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ✅ Initialize ChromaDB with Absolute Path
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name="chat_history")


class JSONMemory:
    """Handles JSON storage for chatbot conversation and tasks."""

    def __init__(self, filename):
        self.filename = os.path.join(DATA_DIR, filename)  # Save JSON inside "data"
        self.ensure_directory_exists()
        # self.db = DatabaseDriver()

    def ensure_directory_exists(self):
        """Ensures the directory of the file exists."""
        os.makedirs(DATA_DIR, exist_ok=True)

    def load_data(self):
        """Loads JSON data from file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: JSON file is corrupted or empty. Resetting data.")
                return {}
        return {}

    def save_data(self, data):
        """Saves data to JSON file."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"✅ Data successfully saved to {self.filename}")

            # # ✅ Corrected: Use `self.filename` instead of `self.file_path`
            # if "flight_search" in self.filename:
            #     self.db.create_flight_search(data)
            # elif "selected_flight" in self.filename:
            #     self.db.create_flight_selection(data)
            #
            # print(f"✅ Data saved to Database.")

            # # ✅ Save to VectorDB
            # store_in_vector_db(data)
            # print(f"✅ Data saved to VectorDB.")

        except Exception as e:
            print(f"❌ Error saving data: {e}")

    def save_necessary_data(self, new_data):
        """Merges new data with existing data and saves to JSON file."""
        existing_data = self.load_data()  # Load previous data

        if not isinstance(existing_data, dict):
            existing_data = {}  # Ensure data format is correct

        # ✅ Merge the new data with existing data
        if isinstance(new_data, dict):
            existing_data.update(new_data)

        self.save_data(existing_data)

    def clear_data(self):
        """Clears the JSON file content."""
        self.save_data({})
        print(f"🗑️ Data in {self.filename} has been cleared.")


def store_in_vector_db(user_id, user_message, bot_response):
    """
    Stores user interactions in ChromaDB for retrieval.
    """
    if user_id is None or user_message is None or bot_response is None:
        raise ValueError("Metadata values cannot be None")

    conversation_text = f"User: {user_message} | Bot: {bot_response}"

    collection.add(
        documents=[conversation_text],
        metadatas=[{"user_id": user_id}],
        ids=[str(user_id) + "_" + str(len(collection.get()["ids"]))]
    )
    print(f"✅ Conversation stored in ChromaDB at {CHROMA_DB_PATH}")


def search_conversation(query):
    """
    Searches for similar past conversations in ChromaDB.
    """
    results = collection.query(
        query_texts=[query],
        n_results=3  # Return top 3 similar results
    )
    return results["documents"]
