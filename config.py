"""
Wednesday AI Assistant — Global Configuration
All settings and constants for every subsystem.
"""

# ─── Assistant Identity ───────────────────────────────────────────
ASSISTANT_NAME = "Wednesday"
WAKE_WORD = "hey wednesday"

# ─── Voice Settings ───────────────────────────────────────────────
VOICE_RATE = 170
VOICE_INDEX = 1  # 0 = male, 1 = female (if available)

# ─── Listener Settings ───────────────────────────────────────────
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 10
LISTEN_LANGUAGE = "en-IN"

# ─── Greeting Responses (varied + natural) ───────────────────────
WAKE_RESPONSES = [
    "Yes boss, how can I help you?",
    "Ji sir, bataiye!",
    "Haan boss, I'm all ears!",
    "Haan boss, kya karna hai?",
    "At your service, boss!",
    "Ready boss! Bolo kya chahiye?",
    "Main hoon boss, bataiye!",
    "Yes sir, aapki Wednesday hazir hai!",
    "Bolo boss, kya help chahiye?",
    "Ji boss, sun rahi hoon!",
]

# ─── Input Mode ──────────────────────────────────────────────────
# "voice" = microphone, "text" = keyboard, "auto" = voice with text fallback
INPUT_MODE = "auto"
TEXT_INPUT_PROMPT = "  🎤 You (type command): "

# ─── Logger Settings ─────────────────────────────────────────────
LOG_DIR = "logs"
LOG_FILE = "logs/wednesday.log"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# ─── Safe Mode ────────────────────────────────────────────────────
SAFE_MODE = True
DANGEROUS_TOOLS = ["delete_file", "press_key", "close_app", "hotkey"]

# ─── State / Context ─────────────────────────────────────────────
CONTEXT_HISTORY_SIZE = 3

# ─── AI Brain ────────────────────────────────────────────────────
OPENROUTER_API_KEY = ""       # Get free key from https://openrouter.ai
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"
HUGGINGFACE_API_KEY = ""      # Get free key from https://huggingface.co
HUGGINGFACE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
AI_RETRY_COUNT = 1
AI_TIMEOUT = 15  # seconds

# ─── Memory ──────────────────────────────────────────────────────
MEMORY_FILE = "memory/memory.json"

# ─── Reminders ───────────────────────────────────────────────────
REMINDERS_FILE = "reminders/reminders.json"
REMINDER_CHECK_INTERVAL = 30  # seconds

# ─── Proactive Conversation ──────────────────────────────────────
IDLE_TIMEOUT_MINUTES = 15
PROACTIVE_ENABLED = True

# ─── Screen Vision ───────────────────────────────────────────────
SCREENSHOT_DIR = "screenshots"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ─── Gesture Control ─────────────────────────────────────────────
GESTURE_SMOOTHING_ALPHA = 0.3
GESTURE_CLICK_COOLDOWN_MS = 400
GESTURE_CONFIDENCE_THRESHOLD = 0.7
GESTURE_FRAME_GUARD = 2  # consecutive frames needed to trigger click
GESTURE_CAMERA_INDEX = 0
