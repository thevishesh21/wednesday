"""
WEDNESDAY AI OS — Unified LLM Client
Abstracts all backends behind ILLMClient.
"""

"""
WEDNESDAY AI OS — Unified LLM Client
Abstracts all backends behind ILLMClient.

FIX CHANGELOG:
  1. OpenRouter key reads from os.environ FIRST (loaded by .env via config_loader)
     so the key is ALWAYS found regardless of config.py load order.
  2. aiohttp sessions created fresh per request and closed immediately —
     zero session leak / "Unclosed client session" warnings gone.
  3. Auto-fallback through free OpenRouter models if one hits rate limits.
  4. Detailed logging at every decision point so you can see exactly
     which backend is chosen and why.
  5. Removed persistent _session attribute entirely — stateless clients.
"""

import json
import os
import time
from typing import Any, List, Optional

import aiohttp

from core.interfaces import ILLMClient, LLMMessage, LLMResponse
from core.exceptions import LLMUnavailableError, LLMResponseError
from core.logger import get_logger
from core.config_loader import cfg

log = get_logger("brain.llm_client")

# ── Free-tier OpenRouter models (tried in order on 402/429) ──────
OPENROUTER_FREE_MODELS: List[str] = [
    "openchat/openchat-3.5-1210:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]

# ── Default timeout settings ──────────────────────────────────────
_OLLAMA_TIMEOUT    = aiohttp.ClientTimeout(total=60, connect=3)
_OPENROUTER_TIMEOUT = aiohttp.ClientTimeout(total=90, connect=10)


# ═════════════════════════════════════════════════════════════════
#  Ollama Client  (Local — Priority 1)
# ═════════════════════════════════════════════════════════════════

class OllamaClient(ILLMClient):
    """Client for a locally running Ollama instance."""

    def __init__(self) -> None:
        self.base_url: str = cfg.ollama_base_url.rstrip("/")
        self.model: str    = cfg.ollama_model

    async def is_available(self) -> bool:
        """Return True if Ollama is reachable within 3 seconds."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=3)
            ) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    ok = resp.status == 200
                    if ok:
                        log.debug(f"Ollama reachable at {self.base_url}")
                    return ok
        except Exception as exc:
            log.debug(f"Ollama not available: {exc}")
            return False

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
    ) -> LLMResponse:
        """Send a chat request to Ollama."""
        if not await self.is_available():
            raise LLMUnavailableError("Ollama is not running or unreachable")

        payload: dict[str, Any] = {
            "model":    self.model,
            "messages": [m.to_dict() for m in messages],
            "stream":   False,
        }
        if tools:
            payload["tools"] = tools

        start = time.time()

        async with aiohttp.ClientSession(timeout=_OLLAMA_TIMEOUT) as session:
            async with session.post(
                f"{self.base_url}/api/chat", json=payload
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise LLMResponseError(
                        f"Ollama HTTP {resp.status}: {body[:300]}"
                    )
                data    = await resp.json()
                content = data.get("message", {}).get("content", "")
                return LLMResponse(
                    text    = content,
                    model   = self.model,
                    tokens  = data.get("eval_count", 0),
                    source  = "ollama",
                    latency = time.time() - start,
                )


# ═════════════════════════════════════════════════════════════════
#  OpenRouter Client  (Cloud — Priority 2)
# ═════════════════════════════════════════════════════════════════

class OpenRouterClient(ILLMClient):
    """
    Client for OpenRouter API (free + paid models).

    Key resolution order (first non-empty wins):
      1. os.environ["OPENROUTER_API_KEY"]   ← set by .env via dotenv
      2. cfg.get("OPENROUTER_API_KEY")      ← value in config.py
    """

    def __init__(self) -> None:
        # ── Resolve API key ───────────────────────────────────
        self.api_key: str = (
            os.environ.get("OPENROUTER_API_KEY", "").strip()
            or cfg.get("OPENROUTER_API_KEY", "").strip()
        )

        # ── Resolve model ─────────────────────────────────────
        self.model: str = (
            os.environ.get("OPENROUTER_MODEL", "").strip()
            or cfg.get("LLM_MODEL", "").strip()
            or OPENROUTER_FREE_MODELS[0]
        )

        # ── Log key status at construction time ───────────────
        if self.api_key:
            log.info(
                f"OpenRouter key loaded ✅  "
                f"model={self.model}  "
                f"key=...{self.api_key[-8:]}"
            )
        else:
            log.warning(
                "OpenRouter API key NOT found. "
                "Add  OPENROUTER_API_KEY=sk-or-...  to your .env file."
            )

    async def is_available(self) -> bool:
        """Return True if an API key is present."""
        if not self.api_key:
            log.warning(
                "OpenRouter unavailable — no API key. "
                "Check your .env file."
            )
            return False
        return True

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
    ) -> LLMResponse:
        """
        Send a chat request to OpenRouter.

        Automatically retries the next free model when the current one
        returns 402 (out of credits) or 429 (rate limited).
        """
        if not await self.is_available():
            raise LLMUnavailableError("OpenRouter API key not configured")

        headers = {
            "Authorization":  f"Bearer {self.api_key}",
            "HTTP-Referer":   "https://wednesday-ai.local",
            "X-Title":        "WEDNESDAY AI OS",
            "Content-Type":   "application/json",
        }

        # Build model priority list: preferred model first, then fallbacks
        models_to_try = [self.model] + [
            m for m in OPENROUTER_FREE_MODELS if m != self.model
        ]

        last_error: str = "Unknown error"

        for model in models_to_try:
            payload: dict[str, Any] = {
                "model":    model,
                "messages": [m.to_dict() for m in messages],
            }

            start = time.time()
            log.debug(f"OpenRouter → trying model: {model}")

            try:
                # Fresh session per request — no persistent session, no leaks
                async with aiohttp.ClientSession(
                    headers=headers,
                    timeout=_OPENROUTER_TIMEOUT,
                ) as session:
                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        json=payload,
                    ) as resp:

                        body = await resp.text()

                        # Rate-limit / quota exhausted — try next model
                        if resp.status in (402, 429):
                            log.warning(
                                f"Model {model} returned {resp.status} "
                                f"(rate limit / quota). Trying next model..."
                            )
                            last_error = f"{model}: HTTP {resp.status}"
                            continue

                        # Auth failure — key is wrong, no point retrying
                        if resp.status == 401:
                            raise LLMUnavailableError(
                                "OpenRouter API key is invalid (HTTP 401). "
                                "Check your .env file."
                            )

                        # Any other non-200
                        if resp.status != 200:
                            raise LLMResponseError(
                                f"OpenRouter HTTP {resp.status}: {body[:300]}"
                            )

                        # Parse JSON
                        try:
                            data = json.loads(body)
                        except json.JSONDecodeError as exc:
                            raise LLMResponseError(
                                f"OpenRouter returned invalid JSON: {exc}. "
                                f"Body: {body[:200]}"
                            ) from exc

                        choices = data.get("choices", [])
                        if not choices:
                            raise LLMResponseError(
                                f"OpenRouter returned no choices. "
                                f"Response: {body[:300]}"
                            )

                        content = (
                            choices[0]
                            .get("message", {})
                            .get("content", "")
                        )
                        tokens  = data.get("usage", {}).get("completion_tokens", 0)
                        latency = time.time() - start

                        log.info(
                            f"OpenRouter ✅  model={model}  "
                            f"tokens={tokens}  latency={latency:.2f}s"
                        )

                        return LLMResponse(
                            text    = content,
                            model   = model,
                            tokens  = tokens,
                            source  = "openrouter",
                            latency = latency,
                        )

            except (LLMResponseError, LLMUnavailableError):
                raise  # Don't retry on hard errors
            except Exception as exc:
                last_error = str(exc)
                log.warning(f"OpenRouter request failed ({model}): {exc}")
                continue  # Try next model

        raise LLMResponseError(
            f"All OpenRouter models exhausted. Last error: {last_error}"
        )


# ═════════════════════════════════════════════════════════════════
#  Client Factory
# ═════════════════════════════════════════════════════════════════

async def get_llm_client() -> ILLMClient:
    """
    Return the best available LLM client.

    Priority:
      1. Ollama  — local, zero latency, no cost (if running)
      2. OpenRouter — cloud, requires OPENROUTER_API_KEY in .env

    Raises:
        LLMUnavailableError: If neither backend is configured/reachable.
    """
    # ── 1. Try Ollama ─────────────────────────────────────────
    ollama = OllamaClient()
    if await ollama.is_available():
        log.info(f"LLM backend selected: Ollama ({ollama.model})")
        return ollama

    # ── 2. Try OpenRouter ─────────────────────────────────────
    openrouter = OpenRouterClient()
    if await openrouter.is_available():
        log.info(f"LLM backend selected: OpenRouter ({openrouter.model})")
        return openrouter

    # ── Nothing available ─────────────────────────────────────
    raise LLMUnavailableError(
        "No LLM backend available. "
        "Option A: Start Ollama → run 'ollama serve' in terminal. "
        "Option B: Add OPENROUTER_API_KEY=sk-or-... to your .env file."
    )