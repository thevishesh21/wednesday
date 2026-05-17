"""
agents/system_agent.py
-----------------------
Handles all system-level commands for Wednesday.

Responds to intents like:
  SYSTEM_CMD  → open/close apps, volume, time, screenshot
  BROWSER_CMD → search web, open URLs, YouTube
"""

import datetime
import logging
from control.apps    import AppController
from control.desktop import DesktopController

logger = logging.getLogger(__name__)


class SystemAgent:
    """
    Executes system and browser commands.
    Returns a human-readable response string.
    """

    def __init__(self):
        self.apps    = AppController()
        self.desktop = DesktopController()
        self._browser = None   # Lazy init — only when needed
        logger.info("SystemAgent ready ✓")

    async def handle(self, intent_action: str, entities: dict, raw_input: str) -> str:
        """
        Route intent to the correct handler.

        Args:
            intent_action: e.g. "open_app", "web_search", "screenshot"
            entities:      extracted params from IntentClassifier
            raw_input:     original user text (fallback for extraction)

        Returns:
            Response string to speak back to user.
        """
        action = intent_action or ""

        # ── System commands ────────────────────────────────────
        if action == "open_app":
            return await self._open_app(entities, raw_input)

        elif action == "close_app":
            return await self._close_app(entities, raw_input)

        elif action == "screenshot":
            return await self._screenshot()

        elif action == "time":
            return self._get_time()

        elif action == "volume":
            return await self._handle_volume(raw_input)

        elif action == "power":
            return await self._handle_power(raw_input)

        # ── Browser commands ───────────────────────────────────
        elif action == "web_search":
            return await self._web_search(raw_input)

        elif action == "open_url":
            return await self._open_url(entities, raw_input)

        elif action == "browse":
            return await self._browse(raw_input)

        else:
            logger.warning(f"SystemAgent: unknown action '{action}'")
            return None   # Return None → orchestrator falls back to LLM

    # ── App handlers ───────────────────────────────────────────

    async def _open_app(self, entities: dict, raw: str) -> str:
        app_name = self._extract_app_name(raw, action="open")
        if not app_name:
            return "Which application would you like me to open?"

        ok, msg = self.apps.open(app_name)
        return msg

    async def _close_app(self, entities: dict, raw: str) -> str:
        app_name = self._extract_app_name(raw, action="close")
        if not app_name:
            return "Which application should I close?"

        ok, msg = self.apps.close(app_name)
        return msg

    def _extract_app_name(self, raw: str, action: str) -> str:
        """Extract app name from raw user text."""
        import re
        # Patterns: "open Chrome", "launch spotify", "close notepad"
        patterns = [
            rf"\b(?:open|launch|start|close|kill|quit)\s+(.+?)(?:\s+(?:for|please|now))?$",
            rf"\b(?:open|launch|start|close|kill|quit)\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw.strip(), re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    # ── System handlers ────────────────────────────────────────

    async def _screenshot(self) -> str:
        ok, result = self.desktop.screenshot()
        if ok:
            return f"Screenshot saved to {result}"
        return "I couldn't take a screenshot."

    def _get_time(self) -> str:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d")
        return f"It's {time_str} on {date_str}."

    async def _handle_volume(self, raw: str) -> str:
        raw_lower = raw.lower()
        if "mute" in raw_lower:
            self.desktop.mute()
            return "Muted."
        elif "unmute" in raw_lower or "volume on" in raw_lower:
            self.desktop.mute()  # Toggle
            return "Unmuted."
        elif "up" in raw_lower or "louder" in raw_lower or "increase" in raw_lower:
            for _ in range(5):
                self.desktop.volume_up()
            return "Volume increased."
        elif "down" in raw_lower or "quieter" in raw_lower or "lower" in raw_lower or "decrease" in raw_lower:
            for _ in range(5):
                self.desktop.volume_down()
            return "Volume decreased."
        return "Should I turn the volume up or down?"

    async def _handle_power(self, raw: str) -> str:
        raw_lower = raw.lower()
        if "shutdown" in raw_lower or "shut down" in raw_lower:
            return "Shutdown cancelled for safety. Please confirm manually."
        elif "restart" in raw_lower:
            return "Restart cancelled for safety. Please confirm manually."
        elif "sleep" in raw_lower:
            import subprocess
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Going to sleep."
        elif "lock" in raw_lower:
            self.desktop.lock_screen()
            return "Locking the screen."
        return "Power action unclear."

    # ── Browser handlers ───────────────────────────────────────

    async def _get_browser(self):
        """Lazy-initialize browser."""
        if self._browser is None:
            from control.browser_control import BrowserController
            self._browser = BrowserController()
            await self._browser.start()
        return self._browser

    async def _web_search(self, raw: str) -> str:
        import re
        # Extract search query
        match = re.search(
            r"(?:search|google|look\s*up|find)\s+(?:for\s+)?(.+?)(?:\s+on\s+(?:google|the\s+web|internet))?$",
            raw.strip(), re.IGNORECASE
        )
        query = match.group(1).strip() if match else raw.strip()

        browser = await self._get_browser()
        ok, msg = await browser.google_search(query)
        return msg

    async def _open_url(self, entities: dict, raw: str) -> str:
        import re
        # Extract URL from text
        match = re.search(r"(https?://\S+|www\.\S+|\S+\.\w{2,})", raw)
        url   = match.group(1) if match else ""

        if not url:
            return "Which website should I open?"

        browser = await self._get_browser()
        ok, msg = await browser.go_to(url)
        return msg

    async def _browse(self, raw: str) -> str:
        raw_lower = raw.lower()

        browser = await self._get_browser()

        if "youtube" in raw_lower:
            # Check if searching or just opening
            import re
            match = re.search(r"(?:search|find|play|look\s+up)\s+(.+?)(?:\s+on\s+youtube)?$",
                              raw, re.IGNORECASE)
            if match:
                ok, msg = await browser.youtube_search(match.group(1))
            else:
                ok, msg = await browser.open_youtube()
            return msg

        elif "gmail" in raw_lower or "email" in raw_lower:
            ok, msg = await browser.open_gmail()
            return msg

        elif "maps" in raw_lower:
            import re
            match = re.search(r"(?:maps?|directions?\s+to)\s+(.+)", raw, re.IGNORECASE)
            loc   = match.group(1) if match else ""
            ok, msg = await browser.open_maps(loc)
            return msg

        elif "github" in raw_lower:
            ok, msg = await browser.open_github()
            return msg

        else:
            return await self._web_search(raw)

    async def shutdown(self):
        """Clean up browser if open."""
        if self._browser and self._browser.is_ready:
            await self._browser.stop()
