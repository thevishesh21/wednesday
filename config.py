"""
Wednesday - Configuration
Loads environment variables and provides app-wide settings.
"""

import os
import logging
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Assistant identity
ASSISTANT_NAME = "Wednesday"
GREETING = "Hi, I am Wednesday, your personal AI assistant. How can I help you?"

# Wake word phrases
WAKE_PHRASES = ["hey wednesday", "wake up wednesday", "wednesday"]
SLEEP_PHRASES = ["go to sleep", "that's all", "goodbye wednesday"]

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
LOG_DIR = os.path.join(DATA_DIR, "logs")

# Ensure data directories exist
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Audio settings
LISTEN_TIMEOUT = 5        # seconds to wait for speech
PHRASE_TIME_LIMIT = 15    # max seconds for a single phrase
ENERGY_THRESHOLD = 300    # microphone energy threshold

# TTS settings
TTS_RATE = 175            # words per minute for pyttsx3
TTS_VOLUME = 1.0          # 0.0 to 1.0

# OpenAI Vision model (for screen awareness)
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

# Contacts database
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")

# Workflows file
WORKFLOWS_FILE = os.path.join(DATA_DIR, "workflows.json")

# Context memory
CONTEXT_MEMORY_FILE = os.path.join(DATA_DIR, "context_memory.json")

# Plugin directory
PLUGIN_DIR = os.path.join(BASE_DIR, "plugins")

# Sound effects directory
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "wednesday.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("Wednesday")
