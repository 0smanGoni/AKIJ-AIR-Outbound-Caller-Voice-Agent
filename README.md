# AKIJ AIR Outbound Caller Voice Agent
This project is a Python-based voice agent for AKIJ AIR, designed to make outbound calls and assist users with flight bookings using LiveKit. It features turn detection, function calling, usage logging, and a modular agent architecture for a seamless booking experience.

## ✨ Features

- Outbound Voice Calls: Initiates calls to users for flight booking assistance.
- Flight Booking Workflow: Collects flight details, passenger information, and confirms bookings.
- Modular Agents: Handles tasks like flight search, passenger details, and booking confirmation separately.
- Natural Interaction: Uses Deepgram for speech-to-text, OpenAI for language processing, and ElevenLabs for text-to-speech.
- Usage Logging: Tracks API usage and agent performance.


## 🔧 Prerequisites
Ensure you have the following installed and ready:

- Python 3.11 or higher
- Git
- LiveKit CLI (for SIP trunk configuration)
- Code editor (e.g., VS Code)
- API keys for:
  - OpenAI
  - Deepgram
  - ElevenLabs
  - DeepSeek
  - AssemblyAI
  - LangSmith (optional)
- A Twilio account for SIP trunk and outbound calling
- A Twilio phone number


## 🚀 Setup Instructions
1. Clone the Repository
git clone https://github.com/0smanGoni/AKIJ-AIR-Outbound-Caller-Voice-Agent.git
cd akij-air-outbound-caller-agent

2. Create a Virtual Environment
Set up a virtual environment to manage dependencies.
Linux/macOS
python3 -m venv venv
source venv/bin/activate

Windows
python3 -m venv venv
venv\Scripts\activate.bat

3. Install Dependencies
Install the required Python packages:
pip install -r requirements.txt

4. Download Required Files
Download necessary data files (e.g., JSON files for memory):
python agent.py download-files


## 🔑 Configuration
Configure the environment by setting up API keys and SIP trunk details.
1. Create the .env File
Copy .env.example (if provided) to .env:
cp .env.example .env

2. Edit the .env File
Add your API keys, URLs, and SIP trunk ID:
# API Keys
- API_KEY=your_api_key
- SECRET_CODE=your_secret_code
- OPENAI_API_KEY=your_openai_key
- DEEPSEEK_API_KEY=your_deepseek_key
- LANGSMITH_API_KEY=your_langsmith_key
- ASSEMBLYAI_API_KEY=your_assemblyai_key
- DEEPGRAM_API_KEY=your_deepgram_key
- ELEVEN_API_KEY=your_elevenlabs_key

# API URLs
- FLIGHT_API_URL=https://serviceapi.innotraveltech.com/flight/search
- DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
- BASE_URL=https://serviceapi.innotraveltech.com/flight/validate

# LiveKit Configuration
- LIVEKIT_API_KEY=your_livekit_api_key
- LIVEKIT_API_SECRET=your_livekit_api_secret
- LIVEKIT_URL=wss://akij-outbound-flight-agent-krjzfyx5.livekit.cloud
- SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id

3. Optional: Use LiveKit CLI
Configure the environment using:
lk app env


## 🏃 Running the Agent
Start the agent in development mode:
python agent.py dev

The agent will run as a worker, waiting for dispatch commands to initiate outbound calls.

### 📞 Setting Up Outbound Calls with Twilio
To enable outbound calls, configure a Twilio SIP trunk and a LiveKit SIP outbound trunk.
1. Create a Twilio SIP Outbound Trunk

- Sign Up: Create a Twilio account.
- Get a Phone Number: Purchase a Twilio phone number.
- Create a SIP Trunk:
  - In the Twilio Console, go to Explore Products > Elastic SIP Trunking > SIP Trunks > Get Started.
  - Create a SIP trunk, name it, and save.


- Configure SIP Termination:
  - Navigate to Termination.
  - Enter a Termination SIP URI.
  - Add a Credentials List with a friendly name, username, and password.



2. Create a LiveKit SIP Outbound Trunk

Prepare the Trunk Configuration:

- Copy outbound-trunk_example.json to outbound-trunk.json.
- Update outbound-trunk.json with your Twilio credentials:
  - name: A descriptive name (e.g., "AKIJ AIR Outbound").
  - address: Your Twilio Termination SIP URI.
  - numbers: Your Twilio phone number (e.g., "+1234567890").
  - auth_username: Username from Twilio Credentials List.
  auth_password: Password from Twilio Credentials List.


- Do not commit outbound-trunk.json to a public repository.

Example outbound-trunk.json:
{
  "trunk": {
    "name": "AKIJ AIR Outbound",
    "address": "your-twilio-sip-uri",
    "numbers": ["+1234567890"],
    "auth_username": "your-username",
    "auth_password": "your-password"
  }
}


Create the Trunk:
lk sip outbound create outbound-trunk.json


Add SIP Trunk ID:

- Copy the SIPTrunkID (e.g., ST_gEnbX26WsU7a) from the CLI output.
- Add it to .env as SIP_OUTBOUND_TRUNK_ID.




## ☎️ Making an Outbound Call
With the agent running, dispatch a call using the LiveKit CLI:
lk dispatch create \
  -new-room \
  -agent-name akij-outbound-flight-agent \
  -metadata '+1234567890'

Replace +1234567890 with the target phone number. The agent will:

- Dial the number.
- Greet the user with a welcome message if answered.
- Assist with flight booking tasks.

Helpful CLI Commands

List projects:
lk project list


List SIP outbound trunks:
lk sip outbound list


List SIP dispatch rules:
lk sip dispatch list




## 🛠️ Troubleshooting

API Key Errors: Verify all keys in .env are correct.
SIP Trunk Issues: Ensure SIP_OUTBOUND_TRUNK_ID is set and outbound-trunk.json has valid Twilio credentials.
Call Failures: Check if the target number is valid and the Twilio phone number is correctly configured.
Dependency Issues: Confirm Python 3.11+ is used and re-run pip install -r requirements.txt.
Logs: Review console output or logs/ directory for errors.


## 🤝 Contributing
Contributions are welcome! To contribute:

Fork the repository.

Create a feature branch:
git checkout -b feature/your-feature


Commit changes:
git commit -m "Add your feature"


Push to the branch:
git push origin feature/your-feature


Open a pull request.


Please follow the Code of Conduct (if available).

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

⭐ Star this repo if you find it useful!📩 For questions, open an issue or contact the maintainers.
