# 🤖 Wednesday — Personal AI Desktop Assistant

> A voice-first AI desktop assistant for Windows, inspired by Siri, Alexa, and Jarvis.
> Control your computer, automate tasks, and get AI-powered answers — all by voice or text.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-PySide6-blueviolet)
![AI](https://img.shields.io/badge/AI-OpenAI%20GPT--4o-orange)

---

## 📖 What is Wednesday?

**Wednesday** is a fully modular, voice-first AI desktop assistant for Windows.

You can talk to it using your microphone or type in the chat window. It understands natural language, controls your computer, answers questions using GPT-4o, and remembers what you told it — all from a sleek floating GUI that stays out of your way.

**Say something like:**

> *"Hey Wednesday, open Chrome and search Python tutorials."*

Wednesday will understand the multi-step command, open Chrome, and run the search — then confirm it in a natural conversational voice.

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🎙️ **Voice Control** | Wake word detection, speech-to-text, natural TTS voice |
| ⌨️ **Text Control** | Floating chat window with typed command support |
| 🧠 **AI Brain** | GPT-4o-powered answers, reasoning, and conversation |
| 📱 **App Control** | Open, launch, and switch any Windows application |
| 🌐 **Web Control** | Open websites, Google search, YouTube search |
| 📁 **File Management** | Create, open, delete, rename, find files and folders |
| 📋 **Clipboard AI** | Summarize, explain, rewrite, or translate copied text |
| ⏰ **Reminders** | Set voice reminders with natural language times |
| 🖥️ **Screen Awareness** | Screenshot + OpenAI Vision — "What is on my screen?" |
| 🗂️ **Contact System** | Contact database, send emails to contacts by name |
| 🔁 **Task Automation** | Multi-step commands — "Open Chrome and search Python" |
| 🧩 **Plugin System** | Drop Python files into `plugins/` to extend abilities |
| 🤖 **Workflows** | "Start work mode" — opens all your work apps at once |
| 💬 **Dictation Mode** | "Start dictation" — types your speech into any window |
| 🧠 **Context Memory** | Remembers the last app, site, command, and session state |
| 💾 **Long-term Memory** | Stores your name, preferences, and personal facts |
| 🔒 **Safety Prompts** | Confirmation required before shutdown, restart, file delete |
| 🖼️ **Modern GUI** | Floating window, animated orb, chat history, always-on-top |
| 🔊 **System Control** | Volume, brightness, mute, lock screen, Task Manager |

---

## 🏗️ Project Architecture

```
wednesday/
│
├── main.py               # Entry point and core orchestrator
├── config.py             # Settings loaded from .env
├── state.py              # Thread-safe assistant state machine
│
├── audio/
│   ├── listener.py       # Microphone input + speech-to-text
│   └── speaker.py        # Text-to-speech (pyttsx3, natural voice)
│
├── brain/
│   ├── ai_brain.py       # OpenAI GPT integration
│   ├── intent_detector.py# AI-powered intent classification
│   ├── personality_engine.py # Conversational response styling
│   ├── task_parser.py    # Multi-step command parser
│   ├── context_memory.py # Session context tracking
│   ├── memory.py         # Short-term + long-term memory
│   └── context.py        # Personal fact extraction
│
├── router/
│   └── command_router.py # Maps intents to skill actions
│
├── skills/
│   ├── app_control.py    # Launch Windows applications
│   ├── web_actions.py    # Browser, Google, YouTube
│   ├── file_control.py   # File and folder management
│   ├── system_control.py # Volume, brightness, shutdown, lock
│   ├── clipboard.py      # Clipboard read, summarize, explain
│   ├── screen_awareness.py # Screenshot + OpenAI Vision
│   ├── contact_manager.py# Contact database and email
│   ├── dictation.py      # Voice typing into active window
│   ├── workflows.py      # Automation workflow runner
│   ├── reminders.py      # Reminder system
│   └── communication.py  # Email via SMTP
│
├── gui/
│   ├── app.py            # Main floating window (PySide6)
│   ├── animations.py     # Animated state orb widget
│   └── theme.py          # Colors and stylesheet
│
├── security/
│   ├── confirmations.py  # Confirmation prompts for risky actions
│   └── voice_lock.py     # Voice identity security (scaffold)
│
├── plugins/              # Drop .py plugin files here
├── wake_word/            # Wake word detector
├── updater/              # Self-update system (scaffold)
│
├── data/
│   ├── contacts.json     # Your contact book
│   ├── workflows.json    # Custom automation workflows
│   ├── memory/           # Long-term memory storage
│   └── logs/             # Assistant log files
│
├── sounds/               # Optional WAV sound effects
│   ├── wake.wav
│   ├── thinking.wav
│   └── confirm.wav
│
└── requirements.txt      # Python dependencies
```

---

## 📋 Requirements

| Requirement | Version |
|---|---|
| **OS** | Windows 10 or Windows 11 |
| **Python** | 3.11 or higher |
| **Microphone** | Optional — typed commands work without one |
| **OpenAI API Key** | Required for AI features |
| **Internet** | Required for OpenAI API calls |

---

## ⚙️ Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/wednesday-ai.git
cd wednesday-ai
```

### Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

### Step 3 — Activate the virtual environment

```bash
.venv\Scripts\activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** PyAudio requires Microsoft C++ Build Tools on some systems.
> If it fails, download the wheel from [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install it manually.

---

## 🔑 OpenAI API Setup

Wednesday uses OpenAI for intent detection, AI answers, and screen vision.

### Step 1 — Create a `.env` file in the project root

```
OPENAI_API_KEY=your_api_key_here
```

### Step 2 — Optional settings

```
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o
```

### Where to get your API key

1. Go to [https://platform.openai.com/](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API Keys**
4. Click **Create new secret key**
5. Copy the key into your `.env` file

> ⚠️ Never commit your `.env` file to version control. It is already listed in `.gitignore`.

---

## 🚀 Running Wednesday

```bash
python main.py
```

The assistant will launch the floating GUI window, position itself at the bottom-right of your screen, and greet you:

> *"Hi, I am Wednesday, your personal AI assistant. How can I help you?"*

---

## 🗣️ Wake Word

Wednesday listens in the background. Say any of these phrases to wake it up:

```
Hey Wednesday
Wake up Wednesday
Wednesday
```

To put it back to sleep:

```
Go to sleep
That's all
Goodbye Wednesday
```

---

## 💬 Example Commands

### 🖥️ App Control

```
Open Notepad
Open Chrome
Open VS Code
Launch Spotify
```

### 🌐 Web & Search

```
Open YouTube
Search Python tutorials
Search machine learning on Google
Open GitHub
```

### 📁 File Management

```
Create file notes.txt
Find my resume
Open my Downloads folder
Open my Documents folder
Delete old_file.txt
```

### 🔊 System Control

```
Volume up
Volume down
Mute
Increase brightness
Decrease brightness
Lock screen
Open Task Manager
Shutdown computer
Restart computer
```

### 🧠 AI Conversation

```
What is artificial intelligence?
Write a Python function to sort a list
Explain quantum computing simply
What time is it in Tokyo?
```

### 📋 Clipboard AI

```
Summarize this
Explain this
Rewrite this
Translate this
```
*(Copy text first, then give the command)*

### 🖥️ Screen Awareness

```
What is on my screen?
Read the text on the screen
Summarize this page
What website is this?
```

### ⏰ Reminders

```
Remind me to drink water at 3 PM
Remind me to call John tomorrow morning
List my reminders
```

### 👤 Contacts

```
Send email to John
Message Mom
List contacts
```

### 🤖 Workflows

```
Start work mode
Start study mode
Start chill mode
```

### ✍️ Dictation

```
Start dictation
```
*(Wednesday will type everything you say into the active window)*
```
Stop dictation
```

### 💾 Memory

```
My name is Vishesh
What is my name?
```

---

## 🖥️ Screen Awareness

Wednesday can see what is on your screen using OpenAI Vision.

**How it works:**
1. Wednesday takes a screenshot of your primary monitor
2. The image is sent to the `gpt-4o` vision model
3. The AI describes what it sees in natural language
4. Wednesday speaks the response aloud

**Supported commands:**

```
What is on my screen?
Read the text on the screen
Summarize this page
What website is this?
What app am I using?
```

> Requires `OPENAI_VISION_MODEL=gpt-4o` in your `.env` file.
> Install `mss` for fast screen capture: `pip install mss`

---

## 🧩 Plugin System

You can extend Wednesday by adding Python files to the `plugins/` directory.

### Create a plugin

```python
# plugins/weather.py

def handle(command: str) -> str:
    """Handle a command passed to this plugin."""
    return "Weather plugin: sunny, 24°C"
```

Wednesday auto-discovers and loads all `.py` files in `plugins/` at startup.

---

## 🔁 Automation Workflows

Workflows let you open a set of apps and websites with one command.

### Built-in workflows

| Command | Opens |
|---|---|
| `Start work mode` | Chrome, VS Code, Outlook |
| `Start study mode` | Chrome, YouTube, Notepad |
| `Start chill mode` | Spotify, YouTube |

### Custom workflows

Add your own to `data/workflows.json`:

```json
{
  "my mode": {
    "description": "My custom setup",
    "steps": [
      {"action": "open_app", "target": "chrome"},
      {"action": "open_app", "target": "discord"},
      {"action": "open_website", "target": "https://github.com"}
    ]
  }
}
```

---

## 🔊 Sound Effects (Optional)

Place WAV files in the `sounds/` directory to enable audio feedback:

| File | Plays when |
|---|---|
| `sounds/wake.wav` | Wednesday starts listening |
| `sounds/thinking.wav` | Processing a command |
| `sounds/confirm.wav` | Speaking a response |

---

## 🖼️ GUI Overview

Wednesday uses a minimal floating window powered by **PySide6**.

| Element | Description |
|---|---|
| **Animated Orb** | Gray = sleeping, Blue = listening, Purple = thinking, Green = speaking |
| **Status Label** | Shows current state: Sleeping / Listening / Thinking / Speaking |
| **Chat History** | Full conversation log with color-coded messages |
| **Input Field** | Type commands without using your microphone |
| **MIC Button** | Click to start listening immediately |
| **Send Button** | Submit typed commands |

The window is **always on top**, **draggable**, and **frameless** — it stays out of your way.

---

## 🔮 Planned Features

- [ ] 🗣️ ElevenLabs or Azure TTS for a more natural voice
- [ ] 📸 Screen interaction — click and fill forms automatically
- [ ] 🔑 Voice biometrics — only respond to the owner's voice
- [ ] 📅 Calendar integration — check schedule, add events
- [ ] 🎵 Spotify / music control plugin
- [ ] 🌤️ Weather plugin
- [ ] 🧠 Persistent AI memory across sessions
- [ ] 🖥️ Multi-monitor screenshot support
- [ ] 📱 Mobile companion app

---

## 🤝 Contributing

Contributions are welcome. Here is how to get started:

1. **Fork** the repository on GitHub
2. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** — keep modules organized in the correct folder
4. **Test** your changes by running `python main.py`
5. **Submit a pull request** with a clear description of what you added

### Guidelines

- Keep each skill in `skills/`
- Keep AI logic in `brain/`
- Do not import GUI code from inside skill modules
- New features should not break existing commands
- Add docstrings to new functions

---

## 📄 License

```
MIT License

Copyright (c) 2025 Wednesday AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

Built with Python · OpenAI · PySide6 · Windows

</div>
