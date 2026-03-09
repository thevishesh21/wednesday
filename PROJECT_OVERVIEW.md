# Wednesday — Personal AI Desktop Assistant (Windows)

A voice-first AI assistant that runs locally on Windows, allowing users to control their computer using natural language commands.

---

## 1. Project Idea

Wednesday is a desktop AI assistant that lets users interact with their Windows computer through voice or text commands instead of navigating menus and clicking through software manually.

Rather than opening apps, searching the web, or managing files by hand, the user simply speaks or types what they need:

- `"Open Chrome"`
- `"Search Python tutorials"`
- `"Send email to John"`
- `"What is artificial intelligence?"`

The assistant understands the intent behind the command, routes it to the appropriate module, executes the task, and responds with speech and text feedback through a graphical interface.

---

## 2. Problem This Project Solves

Modern computers are powerful, but interacting with them still requires manual navigation — opening applications, typing URLs, clicking through settings, managing files in Explorer. Every task demands the user know *where* to go and *how* to do it.

Wednesday introduces an **AI assistant layer** that sits between the user and the operating system. It accepts natural language as input and translates that into system-level actions.

This solves several problems:

- **Friction** — Reduces the number of steps needed to perform common tasks.
- **Accessibility** — Enables hands-free computer control through voice.
- **Complexity** — Hides operating system details behind simple conversational commands.
- **Multitasking** — Allows users to chain actions together (e.g., `"Open Chrome and search Python tutorials"`).

---

## 3. System Overview

The assistant follows a sequential pipeline from user input to system response:

```
User Input (Voice or Text)
        │
        ▼
  Speech Recognition
   (Google Web Speech API via SpeechRecognition library)
        │
        ▼
  Intent Detection
   (Rule-based keyword matching → OpenAI API fallback)
        │
        ▼
  Command Router
   (Maps detected intent to a specific skill and action)
        │
        ▼
  Skill Execution  ──or──  AI Brain
   (System actions,         (OpenAI GPT for general
    app control,             knowledge questions and
    file ops, etc.)          conversation)
        │
        ▼
  Text Response
   (Styled with personality engine prefixes)
        │
        ▼
  Text-to-Speech Output
   (pyttsx3 offline TTS)
        │
        ▼
  GUI Feedback
   (Chat history update, animated orb state change)
```

### Step-by-Step Breakdown

| Step | What Happens |
|------|-------------|
| **User Input** | The user speaks into the microphone or types into the GUI text field. |
| **Speech Recognition** | If voice input, the audio is transcribed to text using the Google Web Speech API through the `SpeechRecognition` library. |
| **Intent Detection** | The transcribed text is classified into one of 13 intent categories. A fast rule-based detector handles obvious commands; ambiguous inputs fall back to an OpenAI API call for classification. |
| **Command Router** | The detected intent (e.g., `open_app`, `search_web`, `file_action`) is mapped to a specific skill module and action function with the correct parameters. |
| **Skill Execution or AI Brain** | If the intent maps to a concrete action (open an app, adjust volume), the corresponding skill module executes it. If the intent is `chat` (a general question), the request is sent to OpenAI GPT for a conversational response. |
| **Text Response** | The result is wrapped with natural conversational phrasing by the personality engine (e.g., `"Sure thing!"`, `"Done."`, `"Here's what I found."`). |
| **Text-to-Speech** | The response text is spoken aloud using `pyttsx3`, an offline TTS engine. |
| **GUI Feedback** | The chat history panel updates with the user's command and the assistant's response. The animated orb changes color and animation based on the current state (listening, thinking, speaking). |

---

## 4. Project Architecture

```
wednesday/
│
├── main.py                    # Entry point — orchestrates the entire assistant
├── config.py                  # Configuration — API keys, paths, constants
├── state.py                   # Thread-safe state machine (sleeping, listening, thinking, speaking)
├── requirements.txt           # Python dependencies
│
├── audio/
│   ├── listener.py            # Microphone input and speech-to-text
│   └── speaker.py             # Text-to-speech output (pyttsx3)
│
├── brain/
│   ├── ai_brain.py            # OpenAI GPT chat completions wrapper
│   ├── intent_detector.py     # Hybrid intent classification (rules + AI)
│   ├── personality_engine.py  # Natural response styling
│   ├── task_parser.py         # Multi-step command splitter
│   ├── context_memory.py      # In-session context tracking
│   ├── memory.py              # Short-term (RAM) + long-term (JSON) memory
│   └── context.py             # Personal fact extraction via regex
│
├── router/
│   └── command_router.py      # Maps intents to skill modules and actions
│
├── skills/
│   ├── system_control.py      # Shutdown, restart, lock, volume, brightness
│   ├── app_control.py         # Open Windows applications by name
│   ├── web_actions.py         # Google search, YouTube, open websites
│   ├── file_control.py        # Create, open, delete, rename, find files
│   ├── clipboard.py           # Read/summarize/explain/rewrite/translate clipboard
│   ├── communication.py       # Send email via SMTP
│   ├── reminders.py           # Set and list reminders (JSON-backed)
│   ├── screen_awareness.py    # Screenshot + OpenAI Vision analysis
│   ├── contact_manager.py     # Contact database with email integration
│   ├── dictation.py           # Voice typing into the active window
│   └── workflows.py           # Automation workflows (work mode, study mode, etc.)
│
├── gui/
│   ├── app.py                 # Main PySide6 floating window with chat interface
│   ├── animations.py          # Animated pulsing orb widget (state-dependent)
│   └── theme.py               # Dark theme colors, fonts, and QSS stylesheet
│
├── security/
│   ├── confirmations.py       # Confirmation prompts before dangerous actions
│   └── voice_lock.py          # Voice authentication placeholder
│
├── plugins/
│   └── __init__.py            # Plugin auto-discovery and loading system
│
├── wake_word/
│   └── detector.py            # Wake word and sleep command detection
│
├── updater/
│   └── self_update.py         # Auto-update placeholder
│
└── data/
    ├── contacts.json          # Contact book (name → email/phone)
    ├── logs/                  # Runtime log files
    └── memory/                # Persistent long-term memory (JSON)
```

### Module Responsibilities

| Module | Role |
|--------|------|
| `audio/` | Handles all speech I/O — capturing microphone input (speech-to-text) and producing spoken responses (text-to-speech). |
| `brain/` | Contains the AI logic — communicating with OpenAI, classifying intents, parsing multi-step commands, maintaining memory, and styling responses. |
| `router/` | Determines how a classified command should be executed by mapping intents to the correct skill module, action, and parameters. |
| `skills/` | Modules that perform actual actions — opening apps, controlling the system, managing files, browsing the web, handling clipboard content, and more. |
| `gui/` | The graphical interface — a dark-themed floating window with an animated state orb, chat history, and text/mic input. |
| `security/` | Safety mechanisms — requires user confirmation before executing dangerous operations like shutdown, file deletion, or sending emails. |
| `plugins/` | Extensibility — allows new features to be added by placing Python files in the `plugins/` directory without modifying the core code. |
| `wake_word/` | Activation — detects wake phrases (e.g., `"Hey Wednesday"`) and sleep commands to control when the assistant is active. |

---

## 5. How the Assistant Thinks

The assistant uses a **hybrid intent detection system** to understand what the user wants:

### Rule-Based Detection (Fast Path)

For common, unambiguous commands, a set of keyword rules classifies the intent instantly without any API call:

```
User: "Open Chrome"
  → Keyword "open" detected
  → Intent: open_app
  → Target: chrome
  → Routed to: skills/app_control.py → open_app("chrome")
```

```
User: "Volume up"
  → Keywords "volume" + "up" detected
  → Intent: system_command
  → Target: volume_up
  → Routed to: skills/system_control.py → volume_up()
```

### AI-Based Detection (Fallback)

For ambiguous or conversational input, the assistant sends the text to OpenAI with a classification prompt that returns structured JSON:

```
User: "What is machine learning?"
  → No rule-based match
  → Sent to OpenAI for classification
  → Intent: chat
  → Routed to: brain/ai_brain.py → ask("What is machine learning?")
  → OpenAI GPT generates a conversational answer
```

### Multi-Step Commands

Compound commands are split into individual tasks before processing:

```
User: "Open Chrome and search Python tutorials"
  → TaskParser splits on "and"
  → Step 1: "Open Chrome" → open_app("chrome")
  → Step 2: "Search Python tutorials" → google_search("Python tutorials")
```

### Safety Checks

Dangerous actions require explicit confirmation before execution:

```
User: "Shut down my computer"
  → Intent: system_command → shutdown
  → Confirmation required: "Are you sure you want to shut down?"
  → User: "Yes"
  → Executes shutdown
```

---

## 6. Key Features

### Voice and Text Interaction
- Wake word activation (`"Hey Wednesday"`) and sleep commands (`"Go to sleep"`)
- Continuous microphone listening with Google Web Speech API
- Text input fallback through the GUI — works without a microphone
- Offline text-to-speech using `pyttsx3`

### Application Control
- Launch 25+ mapped Windows applications by name (Chrome, VS Code, Spotify, Discord, etc.)
- Fallback shell launch for unmapped applications

### Web Browsing
- Google search from voice/text commands
- YouTube open and search
- Open any website by name or URL

### System Control
- Shutdown, restart, sleep, and lock the computer
- Volume up, down, and mute
- Brightness up and down
- Open Task Manager
- Empty the Recycle Bin

### File Management
- Create, open, delete, rename, and find files
- Searches across Desktop, Documents, and Downloads

### Clipboard Intelligence
- Read clipboard contents aloud
- AI-powered summarize, explain, rewrite, and translate operations on clipboard text

### Screen Awareness
- Captures a screenshot and sends it to OpenAI Vision (`gpt-4o`)
- Returns a natural language description of what is visible on screen

### Communication
- Send emails via SMTP with a JSON-backed contact database
- Add, remove, find, and list contacts

### Dictation Mode
- Types spoken words directly into the currently active window

### Automation Workflows
- Built-in workflows: work mode, study mode, chill mode
- Custom workflows defined in JSON

### Memory System
- **Short-term memory** — session-based conversation history (last 50 exchanges)
- **Long-term memory** — persistent JSON storage for user facts and preferences
- **Context tracking** — remembers last app, website, search, file, and contact for follow-up understanding

### Personality and Safety
- Natural conversational response styling with randomized phrases
- Confirmation prompts before dangerous actions (shutdown, delete, send email)

### Plugin System
- Drop a `.py` file into the `plugins/` directory with a `handle()` function
- Automatically discovered and loaded at startup

### GUI
- Dark-themed, frameless, always-on-top floating window
- Animated pulsing orb that changes color and animation based on state
- Chat history panel with color-coded user/assistant messages
- Draggable window with text input and microphone button

---

## 7. Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Python** | Core programming language for the entire project. |
| **OpenAI API** | Powers the AI brain (GPT-4o-mini for conversation, GPT-4o for vision/screen analysis), intent classification fallback, and clipboard intelligence features. |
| **SpeechRecognition** | Captures microphone audio and transcribes speech to text using the Google Web Speech API. |
| **pyttsx3** | Offline text-to-speech engine for Windows — converts response text into spoken audio without requiring an internet connection. |
| **PySide6** | Qt for Python — provides the graphical user interface framework (floating window, chat panel, animated widgets). |
| **pyautogui** | Simulates keyboard input for the dictation feature and serves as a fallback for screenshot capture. |
| **mss** | Fast, cross-platform screenshot capture used for the screen awareness feature. |
| **pycaw** | Windows COM-based audio endpoint control — used for precise volume adjustment. |
| **python-dotenv** | Loads environment variables from a `.env` file for API keys and configuration. |
| **PyAudio** | Audio I/O backend required by the SpeechRecognition library for microphone access. |
| **smtplib** (stdlib) | Sends emails via SMTP protocol — used with Gmail by default. |
| **ctypes** (stdlib) | Calls Windows API functions directly — used for keyboard events, locking the workstation, and emptying the Recycle Bin. |
| **subprocess** (stdlib) | Executes system commands — shutdown, restart, brightness control via PowerShell. |

---

## 8. Example User Interactions

**Launching an application:**
```
User:  "Open YouTube"
Wednesday:  "Sure thing. Opening YouTube."
→ Opens youtube.com in the default browser.
```

**Asking a knowledge question:**
```
User:  "What is Python?"
Wednesday:  "Python is a high-level, interpreted programming language known for
             its readability and versatility. It's widely used in web development,
             data science, AI, and automation."
```

**Web search:**
```
User:  "Search Python tutorials"
Wednesday:  "On it. Searching Google for Python tutorials."
→ Opens Google search results for "Python tutorials" in the browser.
```

**System control:**
```
User:  "Turn the volume up"
Wednesday:  "Done. Volume increased."
→ System volume raised.
```

**Multi-step command:**
```
User:  "Open VS Code and search JavaScript frameworks"
Wednesday:  "Opening VS Code."
            "Searching Google for JavaScript frameworks."
→ Launches VS Code, then opens Google search results.
```

**Clipboard intelligence:**
```
User:  "Summarize what's on my clipboard"
Wednesday:  "Here's a summary of your clipboard: The text discusses three key
             principles of software design — modularity, separation of concerns,
             and single responsibility."
```

**Screen awareness:**
```
User:  "What's on my screen?"
Wednesday:  "You have VS Code open with a Python file. The terminal panel at the
             bottom shows the output of a recent test run."
```

**Workflow automation:**
```
User:  "Start work mode"
Wednesday:  "Starting work mode."
→ Opens Chrome, VS Code, and Outlook in sequence.
```

---

## 9. Future Improvements

- **Better Voice Engine** — Replace the basic pyttsx3 TTS with a neural voice engine for more natural-sounding speech.
- **Advanced Memory System** — Add semantic search over stored memories and cross-session context continuity.
- **Automation Workflows** — Build a visual workflow editor and support time-triggered automations.
- **Computer Vision Features** — Extend screen awareness with element detection, OCR, and UI interaction capabilities.
- **Plugin Marketplace** — Create a repository where users can browse and install community-built plugins.
- **Voice Authentication** — Implement the voice lock feature so the assistant only responds to the authorized user.
- **Scheduled Reminders** — Add time-based reminder triggering with system notifications.
- **Multi-Language Support** — Extend speech recognition and TTS to support languages beyond English.
- **Self-Update System** — Implement the auto-update mechanism for seamless version upgrades.

---

## 10. Project Goal

Wednesday is designed to become a **personal AI operating layer for Windows**.

The long-term vision is to create an assistant that functions as a digital companion — one that understands the user's intent, remembers their preferences, learns from interactions, and executes tasks across the entire operating system.

Instead of the user adapting to the computer, the computer adapts to the user.

The project demonstrates the integration of:

- **Natural language understanding** — Converting human speech into structured actions.
- **System-level automation** — Controlling applications, files, settings, and hardware.
- **AI reasoning** — Answering questions, summarizing content, and making contextual decisions.
- **Conversational memory** — Remembering facts, preferences, and session context.
- **Modular architecture** — A plugin-based design that can grow with new capabilities.

Wednesday is a working prototype of what a personal AI assistant can be when it runs locally, understands context, and has direct access to the operating system.
