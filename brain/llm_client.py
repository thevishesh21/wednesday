"""
WEDNESDAY AI OS — Unified LLM Client
Abstracts all backends behind ILLMClient.
"""

import json
import time
from typing import Any, List, Optional
import aiohttp

from core.interfaces import ILLMClient, LLMMessage, LLMResponse
from core.exceptions import LLMUnavailableError, LLMResponseError
from core.logger import get_logger
from core.config_loader import cfg

log = get_logger("brain.llm_client")

# ═════════════════════════════════════════════════════════════════
#  Ollama Client (Local)
# ═════════════════════════════════════════════════════════════════

class OllamaClient(ILLMClient):
    """Client for local Ollama instances."""
    
    def __init__(self) -> None:
        self.base_url = cfg.ollama_base_url.rstrip('/')
        self.model = cfg.ollama_model
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self._session
        
    async def is_available(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags", timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False
            
    async def chat(self, messages: List[LLMMessage], tools: List[dict] = None) -> LLMResponse:
        """Send a chat request to Ollama."""
        if not await self.is_available():
            raise LLMUnavailableError("Ollama is not running or unreachable")
            
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False
        }
        
        # Tools support (depends on Ollama version and model)
        if tools:
            # We convert our tools schema to Ollama's expected format if needed
            # Most modern Ollama models accept standard OpenAI tool schemas
            payload["tools"] = tools
            
        start_time = time.time()
        
        try:
            session = await self._get_session()
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMResponseError(f"Ollama error: {resp.status} - {text}")
                    
                data = await resp.json()
                content = data.get("message", {}).get("content", "")
                
                # Check for tool calls (Ollama format varies, but usually in message.tool_calls)
                # If there are tool calls, we might need to format them or just return them
                # For Phase 2, we just return the raw string and let the planner parse it if it's JSON
                
                return LLMResponse(
                    text=content,
                    model=self.model,
                    tokens=data.get("eval_count", 0),  # Approx tokens generated
                    source="ollama",
                    latency=time.time() - start_time
                )
        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise
            raise LLMResponseError(f"Error communicating with Ollama: {e}") from e

# ═════════════════════════════════════════════════════════════════
#  OpenRouter Client (Cloud Fallback)
# ═════════════════════════════════════════════════════════════════

class OpenRouterClient(ILLMClient):
    """Client for OpenRouter API (wraps existing ai_brain logic)."""
    
    def __init__(self) -> None:
        self.api_key = cfg.get("OPENROUTER_API_KEY", "")
        self.model = cfg.get("LLM_MODEL", "meta-llama/llama-3-8b-instruct:free")
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://wednesday.ai",
                    "X-Title": "WEDNESDAY"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self._session
        
    async def is_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key.strip())
        
    async def chat(self, messages: List[LLMMessage], tools: List[dict] = None) -> LLMResponse:
        """Send a chat request to OpenRouter."""
        if not await self.is_available():
            raise LLMUnavailableError("OpenRouter API key not configured")
            
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages]
        }
        
        start_time = time.time()
        
        try:
            session = await self._get_session()
            async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMResponseError(f"OpenRouter error: {resp.status} - {text}")
                    
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                
                return LLMResponse(
                    text=content,
                    model=self.model,
                    tokens=data.get("usage", {}).get("completion_tokens", 0),
                    source="openrouter",
                    latency=time.time() - start_time
                )
        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise
            raise LLMResponseError(f"Error communicating with OpenRouter: {e}") from e

# ═════════════════════════════════════════════════════════════════
#  Client Factory
# ═════════════════════════════════════════════════════════════════

async def get_llm_client() -> ILLMClient:
    """
    Return the best available LLM client.
    Priority: Ollama (local) -> OpenRouter (cloud).
    """
    ollama = OllamaClient()
    if await ollama.is_available():
        log.info(f"Using local Ollama client ({ollama.model})")
        return ollama
        
    openrouter = OpenRouterClient()
    if await openrouter.is_available():
        log.info(f"Using cloud OpenRouter client ({openrouter.model})")
        return openrouter
        
    raise LLMUnavailableError("No LLM clients available. Start Ollama or set OPENROUTER_API_KEY.")
