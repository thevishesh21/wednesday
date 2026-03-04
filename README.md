# Wednesday — Personal AI Desktop Assistant (Windows)

A voice-first desktop AI assistant for Windows, powered by OpenAI.

## Features

- Wake word detection ("Hey Wednesday")
- Speech-to-text via SpeechRecognition
- Text-to-speech via pyttsx3
- AI responses via OpenAI (gpt-4o-mini)
- Floating PySide6 GUI with animated state orb
- Skill system: open apps, websites, system control, files, clipboard, email, reminders
- Short-term (RAM) and long-term (JSON) memory
- Confirmation prompts for dangerous actions

## Setup

1. Install dependencies:

```
pip install -r requirements.txt
```

2. Configure your OpenAI API key in `.env`:

```
OPENAI_API_KEY=your_api_key_here
```

3. Run:

```
python main.py
```

## Project Structure

```
wednesday/
├── main.py              # Entry point
├── config.py            # Settings loaded from .env
├── state.py             # Thread-safe assistant state
├── wake_word/           # Wake word detection
├── audio/               # Speech-to-text and text-to-speech
├── brain/               # OpenAI integration and memory
├── router/              # Command routing
├── skills/              # Skill modules
├── gui/                 # PySide6 floating window
├── security/            # Confirmation system
├── updater/             # Self-update placeholder
├── plugins/             # Plugin directory
├── data/                # Runtime data (memory, logs)
└── requirements.txt     # Dependencies
```

## Voice Commands

| Command | Action |
|---|---|
| "Hey Wednesday" | Wake the assistant |
| "Open Chrome" | Launch an application |
| "Search cats on Google" | Google search |
| "Open YouTube" | Open website |
| "Shutdown" | Shut down computer (with confirmation) |
| "My name is Vishesh" | Store personal fact |
| "What is my name?" | Recall stored fact |
| "Remind me to buy milk" | Set a reminder |
| "Go to sleep" | Put assistant to sleep |

## Requirements

- Windows 10/11
- Python 3.11+
- Microphone
- OpenAI API key
