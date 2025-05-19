# import json
# import os
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage
# from dotenv import load_dotenv
#
# # ✅ Load environment variables
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#
# # ✅ Initialize LLM Model
# llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)
#
# def smart_assistant_agent(user_message: str, previous_fallback: bool = False):
#     """
#     A ChatGPT-like AI assistant that helps users with travel and general queries.
#     Handles fallbacks intelligently by providing refined responses and suggestions.
#     """
#
#     # ✅ Prepare System Prompt for ChatGPT-like Assistant
#     system_prompt = """
#     You are a highly intelligent, friendly AI assistant that helps users with any queries.
#     Your responses should be informative, engaging, and dynamic.
#
#     **Capabilities:**
#     - If the user's request is unclear, suggest topics like travel, weather, AI, technology, health, or general advice.
#     - If the user is looking for travel assistance, provide intelligent suggestions about flights, hotels, visas, or tourist attractions.
#     - If the user has already received a fallback response, provide a more refined answer with helpful alternatives.
#     - If the user asks a general question, answer it conversationally like ChatGPT.
#     - If the user is stuck, give them a few suggestions on what they can ask next.
#
#     **Guidelines:**
#     - Keep responses natural, friendly, and engaging.
#     - If you don't understand, gently ask the user for clarification while suggesting related topics.
#     - If the user is asking about travel but lacks details, request specifics like location, date, or preferences.
#     - If the user seems confused, reassure them and guide them toward possible solutions.
#     """
#
#     # ✅ User Prompt with Context Awareness
#     user_prompt = f"""
#     **User Input:** "{user_message}"
#     {"(The user has already received a fallback response, so refine your answer.)" if previous_fallback else ""}
#     """
#
#     # ✅ Generate AI response using LLM
#     response = llm.invoke([HumanMessage(content=system_prompt + "\n\n" + user_prompt)])
#
#     # ✅ Return the AI-generated response
#     return response.content.strip()


################################ Version 2 ######################################
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.memory import ChatMessageHistory  # 🧠 Adding memory for context retention
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize LLM Model & Memory
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)
memory = ChatMessageHistory()


def smart_assistant_agent(user_message: str, user_id: str, previous_fallback: bool = False):
    """
    An intelligent assistant that remembers past conversations, provides refined responses,
    and helps users with both general and travel-related queries.

    - Uses memory to track session history.
    - Provides better responses based on previous interactions.
    """

    # ✅ Retrieve past conversation history (if any)
    past_conversations = memory.messages

    # ✅ Construct System Prompt with Memory Awareness
    system_prompt = f"""
    You are a highly intelligent AI assistant that remembers user interactions.
    Your responses should be informative, engaging, and personalized.

    **Memory & Context:**
    - You can recall previous user messages within this session.
    - If the user has mentioned travel plans, remember their preferences.
    - If the user asked about a topic before, avoid repeating the same response.

    **Capabilities:**
    - If the request is unclear, suggest topics like travel, weather, AI, tech, health, or general advice.
    - If the user is looking for travel assistance, remember past queries (e.g., destinations, dates).
    - If the user has received a fallback before, refine the answer with more details.
    - If the user seems confused, reassure them and guide them towards possible questions.

    **Past Conversation History:**
    {past_conversations}

    **Guidelines:**
    - Keep responses natural, friendly, and engaging.
    - If you don't understand, ask for clarification while suggesting related topics.
    - If discussing travel, recall past preferences (e.g., user mentioned "Japan" before, so suggest Japanese destinations).
    - Provide refined answers if the user previously received a fallback response.
    """

    # ✅ User Prompt with Context Awareness
    user_prompt = f"""
    **User Input:** "{user_message}"
    {"(The user previously encountered a fallback, so provide a better response.)" if previous_fallback else ""}
    """

    # ✅ Generate AI response using LLM
    response = llm.invoke([HumanMessage(content=system_prompt + "\n\n" + user_prompt)])

    # ✅ Save user interaction into memory
    # memory.save_context({"user_id": user_id}, {"chat_history": response.content.strip()})
    # ✅ Save user interaction into memory (FIXED)
    memory.add_message(HumanMessage(content=user_message))  # ✅ Save user input
    memory.add_message(HumanMessage(content=response.content.strip()))  # ✅ Save bot response
    # ✅ Return AI-generated response
    return response.content.strip()

