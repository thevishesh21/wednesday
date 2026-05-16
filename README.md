# Wednesday — AI Desktop Assistant

> *Intelligent. Calm. Slightly witty. Always there.*

Wednesday is a fully autonomous AI assistant for Windows — inspired by JARVIS from Iron Man.
Built in Python. Modular by design. Expandable by nature.

---

## Quick Start

```bash
# 1. Clone / download the project
# 2. Run the setup script
setup.bat

# 3. Add your API key to .env
OPENAI_API_KEY=sk-...

# 4. Launch
python main.py
```

---

## Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Current | Architecture, text REPL, LLM gateway, memory buffer |
| 2 | 🔜 Next | Voice input (Whisper), wake word, TTS (ElevenLabs) |
| 3 | Planned | Long-term vector memory (ChromaDB) |
| 4 | Planned | Desktop automation (pyautogui, Playwright) |
| 5 | Planned | Screen understanding (OCR, multimodal vision) |
| 6 | Planned | Autonomous AI agents (planning, tool calling) |
| 7 | Planned | Optimization (GPU, local models) |
| 8 | Planned | Beautiful UI, system tray, startup service |

---

## Project Structure

```
wednesday/
├── main.py              # Entry point
├── config.yaml          # Tunable settings (edit this)
├── .env                 # API keys (never commit!)
├── requirements.txt
│
├── core/
│   ├── orchestrator.py  # Central brain
│   └── llm_gateway.py   # OpenAI / Claude interface
│
├── voice/
│   ├── listener.py      # STT + wake word (Phase 2)
│   └── speaker.py       # TTS output
│
├── memory/
│   ├── short_term.py    # Conversation buffer
│   └── long_term.py     # Vector DB (Phase 3)
│
├── agents/              # Autonomous agents (Phase 6)
├── control/             # Desktop automation (Phase 4)
├── vision/              # Screen understanding (Phase 5)
├── ui/                  # Tray + panel
└── data/                # Local storage (not committed)
```

---

## Debug Commands (in text mode)

| Command | Action |
|---------|--------|
| `/memory` | Print current conversation buffer |
| `/clear` | Clear short-term memory |
| `quit` | Exit gracefully |

---

## Configuration

Edit `config.yaml` to change behavior without touching code.
Edit `.env` to add API keys.

Key settings:
- `llm.provider` — `openai` or `claude`
- `voice.tts_engine` — `pyttsx3` (local) or `elevenlabs` (natural)
- `voice.whisper_model` — `tiny.en` (fast) to `medium.en` (accurate)
- `log.level` — `DEBUG` for verbose output

---

## Requirements

- Windows 10/11
- Python 3.11+
- OpenAI API key (or Anthropic)
- Microphone (Phase 2+)
