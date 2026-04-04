"""
Wednesday AI Assistant — Task Planner
Sends complex commands to the AI brain and parses the response into
a list of executable steps [{tool, args}].
Falls back to rule-based logic if AI is unavailable.
"""

import json
from utils.logger import get_logger
from brain.ai_brain import ask_ai
from brain.fallback import fallback_response
from tools.registry import list_tools

log = get_logger("planner")

# ── System prompt that forces JSON step output ──────────────────
_SYSTEM_PROMPT = """You are Wednesday, an AI assistant task planner.
Your job is to convert a user command into a JSON list of steps.

Available tools: {tools}

Each step must have: {{"tool": "tool_name", "args": {{"key": "value"}}}}

RULES:
- Output ONLY a valid JSON array, nothing else
- Use only the available tools listed above
- If you can't do something, return: [{{"tool": "speak_response", "args": {{"text": "Sorry boss, ye nahi ho sakta"}}}}]

Example:
User: "Open YouTube and search for Python tutorial"
Output: [
  {{"tool": "open_website", "args": {{"url": "youtube"}}}},
  {{"tool": "search_youtube", "args": {{"query": "python tutorial"}}}}
]"""


def plan_task(command: str) -> dict:
    """
    Plan a task by sending the command to the AI brain.

    Returns:
        {"steps": [...]} — list of tool steps to execute
        {"speak": "..."} — a spoken response (no tool execution needed)
    """
    log.info(f"Planning task: {command}")

    # Build the prompt with available tools
    tools = ", ".join(list_tools())
    system = _SYSTEM_PROMPT.format(tools=tools)
    prompt = f"User command: {command}"

    # Ask AI
    ai_response = ask_ai(prompt, system_prompt=system)

    if ai_response:
        # Try to parse JSON steps
        steps = _parse_steps(ai_response)
        if steps:
            log.info(f"AI planned {len(steps)} steps")
            return {"steps": steps}

        # AI responded but not valid JSON — treat as spoken response
        log.warning("AI response was not valid JSON steps, using as speech.")
        return {"speak": ai_response[:300]}

    # AI failed completely — use fallback
    log.warning("AI unavailable, using fallback.")
    return fallback_response(command)


def _parse_steps(response: str) -> list[dict] | None:
    """
    Parse AI response into a list of step dicts.
    Handles responses that have extra text around the JSON.
    """
    # Try direct parse first
    try:
        steps = json.loads(response)
        if isinstance(steps, list) and all("tool" in s for s in steps):
            return steps
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from the response text
    try:
        start = response.index("[")
        end = response.rindex("]") + 1
        json_str = response[start:end]
        steps = json.loads(json_str)
        if isinstance(steps, list) and all("tool" in s for s in steps):
            return steps
    except (ValueError, json.JSONDecodeError):
        pass

    log.warning(f"Could not parse steps from AI response: {response[:200]}")
    return None
