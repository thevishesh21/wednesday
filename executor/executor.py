"""
Wednesday AI Assistant — Executor
Runs step-by-step plans from the intent router or AI planner.
Handles validation, safe-mode confirmation, retries, and per-step error handling.
"""

from utils.logger import get_logger
from tools import registry
from voice.speaker import speak
from voice.listener import listen
import config

log = get_logger("executor")


def run_plan(steps: list[dict]) -> list[dict]:
    """
    Execute a plan (list of steps) sequentially.

    Each step is: {"tool": "tool_name", "args": {"key": "value"}}

    Returns:
        List of result dicts with success/failure for each step.
    """
    results = []

    for i, step in enumerate(steps, 1):
        tool_name = step.get("tool", "")
        args = step.get("args", {})

        log.info(f"Step {i}/{len(steps)}: {tool_name}({args})")

        # ── 1. Validate tool + args ──────────────────────────
        is_valid, error_msg = registry.validate(tool_name, args)
        if not is_valid:
            log.warning(f"Step {i} validation failed: {error_msg}")
            speak(f"Step {i} skip kar rahi hoon — {error_msg}")
            results.append({"step": i, "tool": tool_name,
                            "success": False, "error": error_msg})
            continue

        # ── 2. Safe mode check ───────────────────────────────
        if config.SAFE_MODE and registry.is_dangerous(tool_name):
            speak(f"Boss, ye risky action hai: {tool_name}. Karoon?")
            confirmation = listen(timeout=5, phrase_limit=5)

            if not confirmation or not _is_confirmed(confirmation):
                log.info(f"Step {i} cancelled by user (safe mode).")
                speak("Theek hai boss, skip kar diya.")
                results.append({"step": i, "tool": tool_name,
                                "success": False, "error": "Cancelled by user"})
                continue

            log.info(f"Step {i} confirmed by user.")

        # ── 3. Execute (with 1 retry on failure) ─────────────
        result = _execute_with_retry(tool_name, args, max_retries=1)
        result["step"] = i
        results.append(result)

        # Report result
        if result["success"]:
            log.info(f"Step {i} completed: {result['result']}")
        else:
            log.error(f"Step {i} failed: {result['error']}")
            speak(f"Step {i} fail ho gaya: {result['error']}")

    return results


def _execute_with_retry(tool_name: str, args: dict,
                        max_retries: int = 1) -> dict:
    """
    Execute a tool with retry logic.

    Returns:
        {"tool": str, "success": bool, "result": any, "error": str|None}
    """
    for attempt in range(1 + max_retries):
        result = registry.execute(tool_name, args)
        result["tool"] = tool_name

        if result["success"]:
            return result

        if attempt < max_retries:
            log.warning(f"Retry {attempt + 1} for {tool_name}...")

    return result


def _is_confirmed(text: str) -> bool:
    """Check if the user's response is an affirmative."""
    affirmatives = [
        "yes", "yeah", "yep", "ya", "yah", "sure", "ok", "okay",
        "haan", "ha", "haa", "ji", "kar do", "karo", "go ahead",
        "do it", "proceed", "confirm", "bilkul", "zaroor",
    ]
    text = text.lower().strip()
    return any(word in text for word in affirmatives)
