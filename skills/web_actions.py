"""
Wednesday - Web Actions Skill
Opens websites and performs web searches.
"""

import webbrowser
import urllib.parse


def google_search(query: str) -> str:
    """Search Google for a query."""
    if not query:
        return "What would you like me to search for?"
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching Google for {query}."


def open_youtube() -> str:
    """Open YouTube."""
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."


def youtube_search(query: str) -> str:
    """Search YouTube for a query."""
    if not query:
        return "What would you like me to search on YouTube?"
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching YouTube for {query}."


def open_website(url: str) -> str:
    """Open a website URL."""
    if not url:
        return "Please tell me which website to open."

    # Add protocol if missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return f"Opening {url}."
    except Exception as e:
        return f"Failed to open website: {e}"
