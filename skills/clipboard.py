"""
Wednesday - Clipboard Skill
Read and summarize clipboard content.
"""


def read_clipboard() -> str:
    """Read the current clipboard text content."""
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        content = result.stdout.strip()
        if content:
            # Limit output for speech
            if len(content) > 500:
                return f"Your clipboard contains: {content[:500]}... and more."
            return f"Your clipboard contains: {content}"
        return "Your clipboard is empty."
    except Exception as e:
        return f"Could not read clipboard: {e}"


def summarize_clipboard(ai_brain=None) -> str:
    """Read clipboard and ask AI to summarize it."""
    content = _get_clipboard_text()
    if content is None:
        return "Could not read clipboard."
    if not content:
        return "Your clipboard is empty, nothing to summarize."

    if ai_brain:
        return ai_brain.ask(f"Please summarize this text concisely: {content}")
    words = content.split()
    if len(words) <= 20:
        return f"Clipboard content: {content}"
    return f"Clipboard has {len(words)} words starting with: {' '.join(words[:20])}..."


def explain_clipboard(ai_brain=None) -> str:
    """Explain the clipboard content using AI."""
    content = _get_clipboard_text()
    if content is None:
        return "Could not read clipboard."
    if not content:
        return "Your clipboard is empty."

    if ai_brain:
        return ai_brain.ask(
            f"Explain the following text in simple terms. Keep it concise for speech: {content}"
        )
    return f"Clipboard contains: {content[:300]}"


def rewrite_clipboard(ai_brain=None) -> str:
    """Rewrite/improve the clipboard content using AI."""
    content = _get_clipboard_text()
    if content is None:
        return "Could not read clipboard."
    if not content:
        return "Your clipboard is empty."

    if ai_brain:
        return ai_brain.ask(
            f"Rewrite and improve the following text. Keep it concise: {content}"
        )
    return "I need AI to rewrite text, but it is not available."


def translate_clipboard(ai_brain=None, target_language: str = "English") -> str:
    """Translate clipboard content using AI."""
    content = _get_clipboard_text()
    if content is None:
        return "Could not read clipboard."
    if not content:
        return "Your clipboard is empty."

    if ai_brain:
        return ai_brain.ask(
            f"Translate the following text to {target_language}. "
            f"Only return the translation: {content}"
        )
    return "I need AI to translate text, but it is not available."


def _get_clipboard_text() -> str | None:
    """Helper to read clipboard text."""
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return None
