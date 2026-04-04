"""
Wednesday AI Assistant — AI Brain
Calls free LLM APIs (OpenRouter → HuggingFace fallback).
Includes retry logic. If both fail, returns None so fallback.py handles it.
"""

import requests
import json
from utils.logger import get_logger
import config

log = get_logger("ai_brain")


def ask_ai(prompt: str, system_prompt: str = "") -> str | None:
    """
    Send a prompt to a free LLM API and return the response text.
    Tries OpenRouter first, then HuggingFace. Retries once on failure.

    Returns:
        Response text string, or None if all APIs fail.
    """
    # Try OpenRouter first
    if config.OPENROUTER_API_KEY:
        for attempt in range(1 + config.AI_RETRY_COUNT):
            result = _call_openrouter(prompt, system_prompt)
            if result:
                return result
            log.warning(f"OpenRouter attempt {attempt + 1} failed.")

    # Fallback to HuggingFace
    if config.HUGGINGFACE_API_KEY:
        for attempt in range(1 + config.AI_RETRY_COUNT):
            result = _call_huggingface(prompt, system_prompt)
            if result:
                return result
            log.warning(f"HuggingFace attempt {attempt + 1} failed.")

    log.error("All AI APIs failed.")
    return None


def _call_openrouter(prompt: str, system_prompt: str = "") -> str | None:
    """Call OpenRouter API."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.OPENROUTER_MODEL,
                "messages": messages,
            },
            timeout=config.AI_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()
            log.info(f"OpenRouter response received ({len(text)} chars)")
            return text
        else:
            log.error(f"OpenRouter HTTP {response.status_code}: {response.text[:200]}")
            return None

    except requests.Timeout:
        log.error("OpenRouter request timed out.")
        return None
    except Exception as e:
        log.error(f"OpenRouter error: {e}")
        return None


def _call_huggingface(prompt: str, system_prompt: str = "") -> str | None:
    """Call HuggingFace Inference API."""
    try:
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:" if system_prompt else prompt

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{config.HUGGINGFACE_MODEL}",
            headers={
                "Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"inputs": full_prompt, "parameters": {"max_new_tokens": 300}},
            timeout=config.AI_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "").strip()
                # Remove the prompt from the response
                if text.startswith(full_prompt):
                    text = text[len(full_prompt):].strip()
                log.info(f"HuggingFace response received ({len(text)} chars)")
                return text
            return None
        else:
            log.error(f"HuggingFace HTTP {response.status_code}: {response.text[:200]}")
            return None

    except requests.Timeout:
        log.error("HuggingFace request timed out.")
        return None
    except Exception as e:
        log.error(f"HuggingFace error: {e}")
        return None
