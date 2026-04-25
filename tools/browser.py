"""
Wednesday AI Assistant — Browser Tool
Opens websites, searches Google/YouTube via the default browser.
"""

import webbrowser
from utils.logger import get_logger

log = get_logger("browser")

# ── Known website shortcuts ─────────────────────────────────────
_SITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "chatgpt": "https://chat.openai.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "whatsapp": "https://web.whatsapp.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "wikipedia": "https://www.wikipedia.org",
}


def open_website(url: str) -> str:
    """
    Open a website URL or known site name in the default browser.

    Args:
        url: Full URL or shortcut name (e.g. "youtube", "google.com")
    """
    url_lower = url.lower().strip()
    log.info(f"Opening website: {url_lower}")

    # ── Check known shortcuts ────────────────────────────────
    full_url = _SITE_MAP.get(url_lower)

    if not full_url:
        # Add https:// if user typed a domain without protocol
        if not url_lower.startswith("http"):
            full_url = f"https://{url_lower}"
        else:
            full_url = url_lower

    try:
        success = webbrowser.open(full_url)
        if success:
            log.info(f"Opened: {full_url}")
            return f"Opening {url}!"
        else:
            return f"FAILED: Browser could not open {url}."
    except Exception as e:
        log.error(f"Failed to open {url}: {e}")
        return f"FAILED: Sorry boss, {url} nahi khul paaya: {e}"


def search_google(query: str) -> str:
    """
    Search Google for a query.

    Args:
        query: Search terms
    """
    log.info(f"Google search: {query}")
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    try:
        success = webbrowser.open(search_url)
        if success:
            log.info(f"Opened Google search: {query}")
            return f"Searching Google for '{query}'!"
        else:
            return f"FAILED: Browser could not open Google search."
    except Exception as e:
        log.error(f"Google search failed: {e}")
        return f"FAILED: Search failed: {e}"


def search_youtube(query: str) -> str:
    """
    Search YouTube for a query.

    Args:
        query: Search terms
    """
    log.info(f"YouTube search: {query}")
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    try:
        success = webbrowser.open(search_url)
        if success:
            log.info(f"Opened YouTube search: {query}")
            return f"Searching YouTube for '{query}'!"
        else:
            return f"FAILED: Browser could not open YouTube search."
    except Exception as e:
        log.error(f"YouTube search failed: {e}")
        return f"FAILED: YouTube search failed: {e}"
