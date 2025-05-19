import os
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Annotated
from time import perf_counter

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm, metrics
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.rtc import DisconnectReason
from livekit.plugins import openai, deepgram, elevenlabs, silero, turn_detector
from livekit import api

from memory.json_memory import JSONMemory

# Import all modular agents and utilities
from agents.agent_selector import select_agent
from agents.smart_assistant_agent import smart_assistant_agent
from agents.passenger_details_agent import collect_passenger_details, extract_passenger_details
from agents.language_detection_agent import detect_language_from_text
from agents.flight_selection_agent import flight_selection_agent
from agents.flight_search_api_agent import flight_search_api_agent
from agents.flight_search_agent import extract_flight_details
from agents.flight_query_agent import flight_query_agent
from agents.confirm_booking_agent import confirm_booking_agent

load_dotenv()
logger = logging.getLogger("outbound-flight-agent")
logger.setLevel(logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FLIGHT_SEARCH_DATA_FILE = os.path.join(DATA_DIR, "flight_search_data.json")
PASSENGER_DATA_FILE = os.path.join(DATA_DIR, "passenger_data.json")
SELECTED_FLIGHT_FILE = os.path.join(DATA_DIR, "selected_flight.json")
FLIGHT_LIST_FILE = os.path.join(DATA_DIR, "flight_list.json")

flight_memory = JSONMemory(FLIGHT_SEARCH_DATA_FILE)
passenger_memory = JSONMemory(PASSENGER_DATA_FILE)
selected_flight_memory = JSONMemory(SELECTED_FLIGHT_FILE)
flight_list_memory = JSONMemory(FLIGHT_LIST_FILE)

WELCOME_MESSAGE = """
Hello! Welcome to AKIJ AIR's booking assistant.  
How can I assist you today?
"""

INSTRUCTIONS = """
You are a friendly and professional flight booking assistant for AKIJ AIR and start communication warmly.  
Your goal is to help users book flights by collecting flight details, passenger information, and confirming bookings.  
- Start by asking for flight details (origin, destination, date, etc.) if not provided.  
- Select a flight from options.
- Once flight details are complete, collect passenger details based on the number of travelers.  
- After passenger details, offer flight options and confirm the booking.  
- Use the provided tools to search flights, save data, and confirm bookings.  
- Respond in a warm, clear, and concise manner.  
"""

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()

    @llm.ai_callable(description="Extract and save flight search details from user input")
    async def extract_flight_info(self, user_input: str):
        logger.info(f"Extracting flight info: {user_input}")
        return extract_flight_details(user_input, user_id="voice_user")

    @llm.ai_callable(description="Select a flight from available options based on user input")
    async def select_flight(self, user_input: str):
        logger.info(f"Selecting flight: {user_input}")
        return flight_selection_agent(user_input)

    @llm.ai_callable(description="Collect passenger details from user input")
    async def collect_passenger_info(self, user_input: str):
        logger.info(f"Collecting passenger info: {user_input}")
        extracted = extract_passenger_details(user_input)
        flight_details = flight_memory.load_data() or {}
        num_adults = flight_details.get("num_adults", 1)
        num_children = flight_details.get("num_children", 0)
        total_passengers = num_adults + num_children
        existing = passenger_memory.load_data() or {"passengers": []}
        passenger_index = next((i for i, p in enumerate(existing.get("passengers", [])) if not all(p.get(f) for f in p)), len(existing.get("passengers", [])))
        return collect_passenger_details(passenger_index=passenger_index, flight_type=flight_details.get("flight_type", "domestic"), **extracted)

    @llm.ai_callable(description="Confirm the flight booking")
    async def confirm_booking(self, user_input: str):
        logger.info(f"Confirming booking for input: {user_input}")
        return confirm_booking_agent()

    @llm.ai_callable(description="Answer general or fallback queries smartly")
    async def smart_assist(self, user_input: str):
        return smart_assistant_agent(user_input, user_id="voice_user")

    @llm.ai_callable(description="Detect the user's language from a given location text")
    async def detect_language(self, location_text: str):
        return detect_language_from_text(location_text)

    @llm.ai_callable(description="Answer flight-related questions from user input")
    async def query_flights(self, user_input: str):
        return flight_query_agent(user_input)

    @llm.ai_callable(description="Use the unified agent selector logic for flexible input handling")
    async def use_selector(self, user_input: str):
        return select_agent(user_input, user_id="voice_user")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=INSTRUCTIONS + "\nUse the provided functions to assist with flight booking tasks step-by-step."
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # SIP Dialing
    phone_number = ctx.job.metadata
    user_identity = "phone_user"
    outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
        raise ValueError("SIP_OUTBOUND_TRUNK_ID is not set or invalid")

    await ctx.api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=ctx.room.name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            participant_identity=user_identity,
        )
    )
    participant = await ctx.wait_for_participant(identity=user_identity)

    # Wait for the user to pick up
    logger.info(f"Dialing {phone_number}")
    start_time = perf_counter()
    while perf_counter() - start_time < 30:
        call_status = participant.attributes.get("sip.callStatus")
        if call_status == "active":
            logger.info("User picked up the call.")
            break
        elif participant.disconnect_reason in [DisconnectReason.USER_REJECTED, DisconnectReason.USER_UNAVAILABLE]:
            logger.info("Call rejected or user unavailable.")
            return
        await asyncio.sleep(0.1)
    else:
        logger.info("Call timeout, user did not pick up.")
        return

    # Setup Agent
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model="nova-2-phonecall"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=elevenlabs.TTS(),
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.5,
        max_endpointing_delay=20.0,
        chat_ctx=initial_ctx,
        fnc_ctx=AssistantFnc(),
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage Summary: {summary}")

    ctx.add_shutdown_callback(log_usage)

    agent.start(ctx.room, participant)
    await agent.say(WELCOME_MESSAGE, allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="akij-outbound-flight-agent",
        )
    )
