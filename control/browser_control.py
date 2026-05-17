"""
control/browser_control.py
---------------------------
Browser automation using Playwright.

Wednesday uses this to execute commands like:
  "Search for Python tutorials on Google"
  "Go to youtube.com"
  "Open Gmail"
  "Search weather in Mumbai"

Setup (MANUAL STEP — run once):
  pip install playwright
  playwright install chromium
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserController:
    """
    Playwright-based browser automation.
    Manages a single persistent browser instance.
    """

    def __init__(self):
        self._browser   = None
        self._page      = None
        self._playwright = None
        self._ready     = False

    async def start(self) -> bool:
        """Launch the browser. Call once at startup."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,      # Visible browser
                args=[
                    "--start-maximized",
                    "--disable-notifications",
                    "--disable-infobars",
                ],
            )
            self._page = await self._browser.new_page()
            await self._page.set_viewport_size({"width": 1280, "height": 800})
            self._ready = True
            logger.info("Browser launched ✓")
            return True

        except ImportError:
            logger.error(
                "Playwright not installed.\n"
                "  Run: pip install playwright\n"
                "  Then: playwright install chromium"
            )
            return False
        except Exception as e:
            logger.error(f"Browser launch failed: {e}")
            return False

    async def stop(self) -> None:
        """Close the browser."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._ready = False
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Browser stop error: {e}")

    # ── Navigation ────────────────────────────────────────────

    async def go_to(self, url: str) -> tuple[bool, str]:
        """Navigate to a URL."""
        if not self._ready:
            ok = await self.start()
            if not ok:
                return False, "Browser not available."

        # Add https if missing
        if not url.startswith("http"):
            url = "https://" + url

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            title = await self._page.title()
            logger.info(f"Navigated to: {url} ({title})")
            return True, f"Opened {url}."
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False, f"Couldn't open {url}."

    async def google_search(self, query: str) -> tuple[bool, str]:
        """Perform a Google search."""
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        url     = f"https://www.google.com/search?q={encoded}"
        ok, msg = await self.go_to(url)
        if ok:
            return True, f"Searching Google for: {query}"
        return ok, msg

    async def youtube_search(self, query: str) -> tuple[bool, str]:
        """Search YouTube."""
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        url     = f"https://www.youtube.com/results?search_query={encoded}"
        return await self.go_to(url)

    async def open_gmail(self) -> tuple[bool, str]:
        return await self.go_to("https://mail.google.com")

    async def open_youtube(self) -> tuple[bool, str]:
        return await self.go_to("https://www.youtube.com")

    async def open_github(self) -> tuple[bool, str]:
        return await self.go_to("https://github.com")

    async def open_maps(self, location: str = "") -> tuple[bool, str]:
        if location:
            import urllib.parse
            return await self.go_to(
                f"https://www.google.com/maps/search/{urllib.parse.quote_plus(location)}"
            )
        return await self.go_to("https://www.google.com/maps")

    # ── Page interaction ──────────────────────────────────────

    async def click_element(self, selector: str) -> tuple[bool, str]:
        """Click a page element by CSS selector."""
        if not self._ready:
            return False, "Browser not open."
        try:
            await self._page.click(selector, timeout=5000)
            return True, "Clicked element."
        except Exception as e:
            return False, f"Click failed: {e}"

    async def type_into(self, selector: str, text: str) -> tuple[bool, str]:
        """Type text into a form field."""
        if not self._ready:
            return False, "Browser not open."
        try:
            await self._page.fill(selector, text)
            return True, f"Typed into field."
        except Exception as e:
            return False, f"Type failed: {e}"

    async def get_page_text(self) -> str:
        """Extract all visible text from the current page."""
        if not self._ready:
            return ""
        try:
            return await self._page.inner_text("body")
        except Exception:
            return ""

    async def get_current_url(self) -> str:
        """Return the current page URL."""
        if not self._ready:
            return ""
        return self._page.url

    async def get_page_title(self) -> str:
        """Return the current page title."""
        if not self._ready:
            return ""
        try:
            return await self._page.title()
        except Exception:
            return ""

    async def scroll_down(self) -> None:
        """Scroll the page down."""
        if self._ready:
            await self._page.keyboard.press("PageDown")

    async def go_back(self) -> tuple[bool, str]:
        """Navigate back."""
        if not self._ready:
            return False, "Browser not open."
        await self._page.go_back()
        return True, "Went back."

    async def screenshot(self) -> Optional[bytes]:
        """Take a screenshot of the current browser page."""
        if not self._ready:
            return None
        try:
            return await self._page.screenshot()
        except Exception:
            return None

    @property
    def is_ready(self) -> bool:
        return self._ready
