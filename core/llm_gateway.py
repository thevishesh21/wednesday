"""
core/llm_gateway.py
--------------------
Unified LLM interface supporting FREE providers:

  FREE OPTIONS (no credit card):
  ┌─────────────────────────────────────────────────────────┐
  │  groq     → Groq API   — fastest, free tier             │
  │  gemini   → Google AI  — 1M tokens/day free             │
  │  ollama   → Local AI   — 100% free, runs on your PC     │
  │  openai   → OpenAI     — paid only                      │
  │  claude   → Anthropic  — paid only                      │
  └─────────────────────────────────────────────────────────┘

HOW TO GET FREE KEYS:
  Groq:   https://console.groq.com  → Create account → API Keys
  Gemini: https://aistudio.google.com/app/apikey → Get API Key
  Ollama: https://ollama.com/download → Install → run: ollama pull llama3
"""

import asyncio
import time
from typing import Optional
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class LLMGateway:
    """
    Wraps multiple LLM providers behind a single clean async interface.

    Usage:
        gateway = LLMGateway()
        response = await gateway.chat(messages=[...])
    """

    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]

    def __init__(self):
        self._openai_client   = None
        self._anthropic_client = None
        self._groq_client     = None
        self._gemini_model    = None
        self._total_calls     = 0
        self._total_tokens    = 0
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize the configured provider's client."""
        provider = settings.llm.provider
        logger.info(f"Initializing LLM provider: {provider}")

        if provider == "groq":
            self._init_groq()
        elif provider == "gemini":
            self._init_gemini()
        elif provider == "ollama":
            logger.info("Ollama selected — no client init needed (HTTP calls).")
        elif provider == "openai":
            self._init_openai()
        elif provider == "claude":
            self._init_claude()
        else:
            logger.error(f"Unknown provider '{provider}'. Use: groq, gemini, ollama, openai, claude")

    # ── Provider init ──────────────────────────────────────────────

    def _init_groq(self) -> None:
        if not settings.groq_api_key:
            logger.error(
                "GROQ_API_KEY missing!\n"
                "  1. Go to: https://console.groq.com\n"
                "  2. Sign up free (no credit card)\n"
                "  3. Click API Keys → Create API Key\n"
                "  4. Add to .env:  GROQ_API_KEY=gsk_..."
            )
            return
        try:
            from groq import AsyncGroq
            self._groq_client = AsyncGroq(api_key=settings.groq_api_key)
            logger.info(f"Groq client ready (model={settings.llm.groq_model}) ✓")
        except ImportError:
            logger.error("groq package not installed. Run: pip install groq")

    def _init_gemini(self) -> None:
        if not settings.gemini_api_key:
            logger.error(
                "GEMINI_API_KEY missing!\n"
                "  1. Go to: https://aistudio.google.com/app/apikey\n"
                "  2. Sign in with Google account (free)\n"
                "  3. Click 'Create API Key'\n"
                "  4. Add to .env:  GEMINI_API_KEY=AIza..."
            )
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_model = genai.GenerativeModel(
                model_name=settings.llm.gemini_model,
                system_instruction=settings.persona,
            )
            logger.info(f"Gemini client ready (model={settings.llm.gemini_model}) ✓")
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")

    def _init_openai(self) -> None:
        if not settings.has_openai():
            logger.error("OPENAI_API_KEY missing or invalid.")
            return
        try:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.llm.timeout,
                max_retries=0,
            )
            logger.info(f"OpenAI client ready (model={settings.llm.openai_model}) ✓")
        except ImportError:
            logger.error("openai not installed. Run: pip install openai")

    def _init_claude(self) -> None:
        if not settings.has_anthropic():
            logger.error("ANTHROPIC_API_KEY missing or invalid.")
            return
        try:
            from anthropic import AsyncAnthropic
            self._anthropic_client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.llm.timeout,
                max_retries=0,
            )
            logger.info(f"Anthropic client ready (model={settings.llm.claude_model}) ✓")
        except ImportError:
            logger.error("anthropic not installed. Run: pip install anthropic")

    # ── Main chat method ───────────────────────────────────────────

    async def chat(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send conversation to LLM and return the response text.

        Args:
            messages:      List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: Override persona
            temperature:   Override temperature
            max_tokens:    Override max_tokens

        Returns:
            Assistant reply as plain string. Never raises.
        """
        sys_prompt = system_prompt or settings.persona
        temp       = temperature if temperature is not None else settings.llm.temperature
        tokens     = max_tokens or settings.llm.max_tokens
        provider   = settings.llm.provider

        for attempt in range(self.MAX_RETRIES):
            try:
                t0 = time.monotonic()

                if provider == "groq":
                    result, usage = await self._groq_chat(messages, sys_prompt, temp, tokens)
                elif provider == "gemini":
                    result, usage = await self._gemini_chat(messages, sys_prompt, temp, tokens)
                elif provider == "ollama":
                    result, usage = await self._ollama_chat(messages, sys_prompt, temp, tokens)
                elif provider == "openai":
                    result, usage = await self._openai_chat(messages, sys_prompt, temp, tokens)
                elif provider == "claude":
                    result, usage = await self._claude_chat(messages, sys_prompt, temp, tokens)
                else:
                    return f"Unknown provider: {provider}. Set provider in config.yaml"

                elapsed = time.monotonic() - t0
                self._total_calls  += 1
                self._total_tokens += usage
                logger.info(
                    f"LLM({provider}) {elapsed:.2f}s | tokens~{usage} | "
                    f"reply: '{result[:60]}...'"
                )
                return result

            except Exception as e:
                err = str(e)
                is_last = attempt == self.MAX_RETRIES - 1

                # Don't retry auth errors
                if any(code in err for code in ("401", "403", "invalid_api_key", "API key")):
                    logger.error(f"Auth error — check your API key in .env: {e}")
                    return (
                        "I can't authenticate with my AI provider. "
                        "Please check your API key in the .env file."
                    )

                # Rate limit — wait longer
                if "429" in err or "rate_limit" in err.lower():
                    wait = 10 if is_last else self.RETRY_DELAYS[attempt] * 3
                    logger.warning(f"Rate limit hit. Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if is_last:
                    logger.error(f"LLM failed after {self.MAX_RETRIES} attempts: {e}")
                    return (
                        "I'm having trouble reaching my AI brain right now. "
                        "Please check your internet connection and try again."
                    )

                delay = self.RETRY_DELAYS[attempt]
                logger.warning(f"LLM attempt {attempt+1} failed ({e}). Retrying in {delay}s...")
                await asyncio.sleep(delay)

        return "Something went wrong. Please try again."

    # ── Provider implementations ───────────────────────────────────

    async def _groq_chat(
        self, messages: list, system_prompt: str, temperature: float, max_tokens: int
    ) -> tuple:
        """Groq API — free, extremely fast (LPU hardware)."""
        if not self._groq_client:
            return "Groq client not initialized. Check GROQ_API_KEY in .env", 0

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await self._groq_client.chat.completions.create(
            model=settings.llm.groq_model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text   = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text.strip(), tokens

    async def _gemini_chat(
        self, messages: list, system_prompt: str, temperature: float, max_tokens: int
    ) -> tuple:
        """Google Gemini API — free 1M tokens/day."""
        if not self._gemini_model:
            return "Gemini not initialized. Check GEMINI_API_KEY in .env", 0

        import google.generativeai as genai

        # Convert messages to Gemini format
        history = []
        last_user_msg = ""
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if msg == messages[-1] and msg["role"] == "user":
                last_user_msg = msg["content"]
                break
            history.append({"role": role, "parts": [msg["content"]]})

        # Run in executor (Gemini SDK is sync)
        def _call():
            chat = self._gemini_model.start_chat(history=history)
            resp = chat.send_message(
                last_user_msg,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return resp.text

        text = await asyncio.get_event_loop().run_in_executor(None, _call)
        return text.strip(), len(text) // 4  # Approximate tokens

    async def _ollama_chat(
        self, messages: list, system_prompt: str, temperature: float, max_tokens: int
    ) -> tuple:
        """
        Ollama — runs AI models 100% locally on your PC.

        Setup:
          1. Download Ollama: https://ollama.com/download
          2. Install and run it
          3. Open terminal: ollama pull llama3
          4. Set in config.yaml: llm.provider: ollama
        """
        import httpx

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model":    settings.llm.ollama_model,
            "messages": full_messages,
            "stream":   False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{settings.llm.ollama_base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        text = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count", len(text) // 4)
        return text.strip(), tokens

    async def _openai_chat(
        self, messages: list, system_prompt: str, temperature: float, max_tokens: int
    ) -> tuple:
        if not self._openai_client:
            return "OpenAI not configured.", 0
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await self._openai_client.chat.completions.create(
            model=settings.llm.openai_model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text   = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text.strip(), tokens

    async def _claude_chat(
        self, messages: list, system_prompt: str, temperature: float, max_tokens: int
    ) -> tuple:
        if not self._anthropic_client:
            return "Anthropic not configured.", 0
        response = await self._anthropic_client.messages.create(
            model=settings.llm.claude_model,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text   = response.content[0].text if response.content else ""
        tokens = (response.usage.input_tokens + response.usage.output_tokens
                  if response.usage else 0)
        return text.strip(), tokens

    # ── Utilities ──────────────────────────────────────────────────

    def switch_provider(self, provider: str) -> None:
        logger.info(f"Switching provider: {settings.llm.provider} → {provider}")
        settings.llm.provider = provider
        self._init_clients()

    def get_stats(self) -> dict:
        return {
            "provider":     settings.llm.provider,
            "total_calls":  self._total_calls,
            "total_tokens": self._total_tokens,
        }