"""
Wednesday AI Assistant — Intent Router
Fast keyword-matching shortcuts that bypass the AI brain.
Simple commands like "open youtube" execute directly without an API call.
"""

import re
from utils.logger import get_logger

log = get_logger("intent_router")


# ═════════════════════════════════════════════════════════════════
#  Intent Shortcut Rules
#  Each rule: (pattern_regex, tool_name, arg_builder_func)
# ═════════════════════════════════════════════════════════════════

def _build_routes():
    """
    Build and return the list of intent routes.
    Each route is: (compiled_regex, tool_name, args_builder)
    where args_builder takes the regex match and returns a dict.
    """
    routes = [
        # ── Open apps ────────────────────────────────────────
        (r"(?:open|launch|start|run)\s+(.+)",
         "open_app",
         lambda m: {"name": m.group(1).strip()}),

        # ── Close apps ───────────────────────────────────────
        (r"(?:close|quit|exit|kill|stop)\s+(.+)",
         "close_app",
         lambda m: {"name": m.group(1).strip()}),

        # ── Open website (explicit) ──────────────────────────
        (r"(?:go to|visit|open website|open site)\s+(.+)",
         "open_website",
         lambda m: {"url": m.group(1).strip()}),

        # ── Search Google ────────────────────────────────────
        (r"(?:search|google|look up|find)\s+(?:for\s+)?(.+?)(?:\s+on\s+google)?$",
         "search_google",
         lambda m: {"query": m.group(1).strip()}),

        # ── Search YouTube ───────────────────────────────────
        (r"(?:play|search youtube for|youtube search|find on youtube)\s+(.+)",
         "search_youtube",
         lambda m: {"query": m.group(1).strip()}),

        (r"(?:search|find|look up)\s+(.+?)\s+on\s+youtube",
         "search_youtube",
         lambda m: {"query": m.group(1).strip()}),

        # ── Type text ────────────────────────────────────────
        (r"(?:type|write|enter)\s+[\"']?(.+?)[\"']?\s*$",
         "type_text",
         lambda m: {"text": m.group(1).strip()}),

        # ── Press key ────────────────────────────────────────
        (r"press\s+(.+)",
         "press_key",
         lambda m: {"key": m.group(1).strip()}),

        # ── Mouse click ──────────────────────────────────────
        (r"click(?:\s+at)?\s+(\d+)\s+(\d+)",
         "mouse_click",
         lambda m: {"x": int(m.group(1)), "y": int(m.group(2))}),

        (r"(?:right click|right-click)\s*(?:at\s+)?(\d+)?\s*(\d+)?",
         "mouse_click",
         lambda m: {"x": int(m.group(1)) if m.group(1) else None,
                     "y": int(m.group(2)) if m.group(2) else None,
                     "button": "right"}),

        # ── Mouse move ───────────────────────────────────────
        (r"move\s+(?:mouse\s+)?(?:to\s+)?(\d+)\s+(\d+)",
         "move_mouse",
         lambda m: {"x": int(m.group(1)), "y": int(m.group(2))}),

        # ── Scroll ───────────────────────────────────────────
        (r"scroll\s+(up|down)(?:\s+(\d+))?",
         "scroll",
         lambda m: {"amount": int(m.group(2) or 3) * (1 if m.group(1) == "up" else -1)}),

        # ── Mouse position ───────────────────────────────────
        (r"(?:where is|mouse position|cursor position)",
         "screenshot_position",
         lambda m: {}),

        # ── Volume control ───────────────────────────────────
        (r"(?:volume up|increase volume)",
         "press_key",
         lambda m: {"key": "volumeup"}),

        (r"(?:volume down|decrease volume)",
         "press_key",
         lambda m: {"key": "volumedown"}),

        (r"(?:mute|unmute|toggle mute)",
         "press_key",
         lambda m: {"key": "volumemute"}),
    ]

    # Compile regex patterns
    return [(re.compile(pattern, re.IGNORECASE), tool, builder)
            for pattern, tool, builder in routes]


# ── Build routes at import time ─────────────────────────────────
_ROUTES = _build_routes()


def route(command: str) -> list[dict] | None:
    """
    Try to match a command against intent shortcuts.

    Args:
        command: The user's command text (lowercase)

    Returns:
        A list of step dicts [{"tool": name, "args": {...}}] if matched,
        or None if no shortcut matches (command should go to AI brain).
    """
    command = command.strip().lower()

    for pattern, tool_name, args_builder in _ROUTES:
        match = pattern.match(command)
        if match:
            args = args_builder(match)
            log.info(f"Intent matched: '{command}' → {tool_name}({args})")
            return [{"tool": tool_name, "args": args}]

    log.debug(f"No intent match for: '{command}'")
    return None
