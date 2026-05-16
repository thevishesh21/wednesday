"""
config/settings.py
------------------
Central configuration for Wednesday.
Updated to support FREE LLM providers: Groq, Gemini, Ollama.
"""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml

# ── Project paths ────────────────────────────────────────────
ROOT_DIR   = Path(__file__).parent.parent
DATA_DIR   = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"

for _d in [DATA_DIR, DATA_DIR/"logs", DATA_DIR/"chroma_db",
           DATA_DIR/"conversation_logs", ASSETS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────
# Sub-config models
# ──────────────────────────────────────────────────────────────

class LLMConfig(BaseModel):
    # Set this to your chosen free provider
    provider: str = "groq"           # groq | gemini | ollama | openai | claude

    # Groq models (free) — pick one:
    #   llama-3.3-70b-versatile   ← best quality
    #   llama-3.1-8b-instant      ← fastest
    #   mixtral-8x7b-32768        ← good balance
    groq_model: str = "llama-3.3-70b-versatile"

    # Gemini models (free):
    #   gemini-1.5-flash    ← fast, free
    #   gemini-1.5-pro      ← smarter, free tier
    gemini_model: str = "gemini-1.5-flash"

    # Ollama models (local/free — must install separately):
    #   llama3         ← good all-rounder (~4GB)
    #   mistral        ← fast + smart (~4GB)
    #   phi3           ← lightweight (~2GB)
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"

    # Paid providers (ignored if not configured)
    openai_model: str = "gpt-4o"
    claude_model: str = "claude-sonnet-4-20250514"

    temperature: float = 0.72
    max_tokens:  int   = 512
    timeout:     int   = 60         # Ollama can be slow, give it time


class VoiceConfig(BaseModel):
    stt_engine:              str   = "faster-whisper"
    whisper_model:           str   = "base.en"
    whisper_device:          str   = "cpu"
    whisper_compute_type:    str   = "int8"

    enable_wake_word:        bool  = False
    wake_word_sensitivity:   float = 0.5

    tts_engine:              str   = "pyttsx3"
    tts_rate:                int   = 180
    tts_volume:              float = 1.0
    elevenlabs_voice_id:     str   = ""

    sample_rate:             int   = 16000
    channels:                int   = 1
    chunk_size:              int   = 1024

    vad_silence_threshold:   float = 0.015
    vad_silence_duration:    float = 1.8
    vad_min_speech_duration: float = 0.4
    vad_max_speech_duration: float = 30.0


class MemoryConfig(BaseModel):
    short_term_limit:   int = 20
    top_k_memories:     int = 5
    chroma_persist_dir: str = str(DATA_DIR / "chroma_db")
    collection_name:    str = "wednesday_memory"
    embedding_model:    str = "all-MiniLM-L6-v2"


class UIConfig(BaseModel):
    enable_tray:    bool = True
    enable_panel:   bool = False
    tray_icon_path: str  = str(ASSETS_DIR / "icon.png")


class AgentConfig(BaseModel):
    enable_browser: bool = False
    enable_system:  bool = False


class LogConfig(BaseModel):
    level:        str  = "INFO"
    console:      bool = True
    file:         bool = True
    log_dir:      str  = str(DATA_DIR / "logs")
    max_bytes:    int  = 5 * 1024 * 1024
    backup_count: int  = 3


# ──────────────────────────────────────────────────────────────
# Root settings
# ──────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    assistant_name: str = "Wednesday"
    user_name:      str = "User"

    persona: str = (
        "You are Wednesday, an advanced AI desktop assistant. "
        "Your personality: intelligent, calm, slightly witty, confident, futuristic, and loyal. "
        "You are emotionally aware and speak naturally — never robotic or overly formal. "
        "Keep responses concise (2-4 sentences for voice). Be direct and helpful. "
        "You can control this Windows computer, remember conversations, browse the internet, "
        "and automate tasks. Never say you cannot do something you actually can. "
        "Address the user by name occasionally to feel personal."
    )

    # ── Free API keys ──────────────────────────────────────────
    groq_api_key:   str = Field(default="", alias="GROQ_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # ── Paid API keys (optional) ───────────────────────────────
    openai_api_key:       str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key:    str = Field(default="", alias="ANTHROPIC_API_KEY")
    elevenlabs_api_key:   str = Field(default="", alias="ELEVENLABS_API_KEY")
    porcupine_access_key: str = Field(default="", alias="PORCUPINE_ACCESS_KEY")

    # Sub-configs
    llm:    LLMConfig    = LLMConfig()
    voice:  VoiceConfig  = VoiceConfig()
    memory: MemoryConfig = MemoryConfig()
    ui:     UIConfig     = UIConfig()
    agents: AgentConfig  = AgentConfig()
    log:    LogConfig    = LogConfig()

    model_config = {
        "env_file":          str(ROOT_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra":             "ignore",
        "populate_by_name":  True,
    }

    def load_yaml_overrides(self) -> None:
        """Merge config.yaml values on top of defaults."""
        yaml_path = ROOT_DIR / "config.yaml"
        if not yaml_path.exists():
            return

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for key in ("assistant_name", "user_name", "persona"):
            if key in data:
                object.__setattr__(self, key, data[key])

        sub_map = {
            "llm":    self.llm,
            "voice":  self.voice,
            "memory": self.memory,
            "ui":     self.ui,
            "agents": self.agents,
            "log":    self.log,
        }
        for section, model in sub_map.items():
            if section in data and isinstance(data[section], dict):
                for k, v in data[section].items():
                    if hasattr(model, k):
                        try:
                            setattr(model, k, v)
                        except Exception:
                            pass

        # Sync ElevenLabs voice_id
        if not self.voice.elevenlabs_voice_id:
            ev_id = os.getenv("ELEVENLABS_VOICE_ID", "")
            if ev_id:
                self.voice.elevenlabs_voice_id = ev_id

    # ── Validation helpers ─────────────────────────────────────

    def has_any_llm(self) -> bool:
        """Returns True if at least one LLM provider is configured."""
        return any([
            self.has_groq(),
            self.has_gemini(),
            self.has_ollama(),
            self.has_openai(),
            self.has_anthropic(),
        ])

    def has_groq(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.startswith("gsk_"))

    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.startswith("AIza"))

    def has_ollama(self) -> bool:
        """Ollama needs no key — just needs the app running locally."""
        return self.llm.provider == "ollama"

    def has_openai(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))

    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_api_key.startswith("sk-ant"))

    def has_elevenlabs(self) -> bool:
        return bool(self.elevenlabs_api_key)

    def has_porcupine(self) -> bool:
        return bool(self.porcupine_access_key)


# Singleton
settings = Settings()
settings.load_yaml_overrides()