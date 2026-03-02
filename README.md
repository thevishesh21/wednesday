# Wednesday AI Assistant

A premium, futuristic Windows desktop AI assistant powered by GPT-4o.

---

## Features

- **Wake Word** — "Hey Wednesday" / "Wake up Wednesday" — always listening in low-power mode
- **Voice I/O** — OpenAI Whisper (STT) + OpenAI TTS Nova voice
- **GPT-4o Brain** — Intent detection via tool-calling, not keyword matching
- **Tool System** — Launch apps, system control, send email — fully extensible
- **Futuristic GUI** — Animated orb, waveform visualiser, glassmorphism panels, 60fps

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-repo/wednesday
cd wednesday

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Fill in OPENAI_API_KEY and optional SMTP credentials

# 4. Run
python main.py
```

---

## Project Structure

```
wednesday/
├── main.py               Entry point
├── config.py             Central configuration (env-driven)
├── core/
│   ├── assistant.py      State machine + orchestration
│   ├── events.py         Thread-safe event bus
│   ├── orchestrator.py   Middleware pipeline
│   └── context_manager.py  Context window management
├── brain/
│   ├── llm_client.py     OpenAI Chat + tool-calling
│   ├── tool_registry.py  Central tool registry
│   ├── intent_parser.py  Supplemental NLU helpers
│   └── prompt_templates.py  System prompt
├── voice/
│   ├── wake_word.py      Always-listening detector
│   ├── speech_to_text.py Whisper API transcription
│   └── text_to_speech.py OpenAI TTS + pygame playback
├── tools/
│   ├── base_tool.py      Abstract tool interface
│   ├── app_launcher.py   Open Windows applications
│   ├── system_tools.py   Time, shutdown, volume, lock
│   ├── email_tool.py     SMTP email sender
│   └── messaging_tool.py SMS stub (Twilio-ready)
├── gui/
│   ├── main_window.py    Frameless PyQt6 window
│   ├── widgets.py        OrbWidget, WaveformWidget, etc.
│   └── theme.py          Design tokens
├── memory/
│   ├── short_term.py     Rolling conversation buffer
│   ├── long_term.py      JSON-backed persistent facts
│   └── storage.py        Low-level JSON helpers
├── services/
│   ├── logger.py         Rotating file + console logger
│   ├── settings_manager.py  QSettings persistence
│   └── task_queue.py     ThreadPoolExecutor wrapper
├── data/                 Runtime data (logs, memory)
├── assets/               Icons, sounds, images
└── build/
    ├── build_exe.spec    PyInstaller spec
    └── installer_config.iss  Inno Setup installer
```

---

## Building the .exe

```bash
# From project root
pyinstaller build/build_exe.spec

# Output: dist/Wednesday.exe
```

Then run `build/installer_config.iss` through Inno Setup to produce a polished installer.

---

## Adding New Tools

```python
# tools/my_tool.py
from tools.base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self): return "my_tool"

    @property
    def description(self): return "Does something useful."

    def parameters_schema(self):
        return {
            "type": "object",
            "properties": { "param": {"type": "string"} },
            "required": ["param"],
        }

    def execute(self, param: str, **_) -> str:
        return f"Did the thing with {param}"
```

Then register in `core/assistant.py`:
```python
from tools.my_tool import MyTool
self._registry.register(MyTool())
```

---

## Wake Phrases

| Phrase | Action |
|--------|--------|
| "Hey Wednesday" | Wake |
| "Wake up Wednesday" | Wake |
| "Go to sleep" | Sleep |
| "That's all" | Sleep |

---

## License
MIT