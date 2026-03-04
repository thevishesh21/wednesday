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
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        content = result.stdout.strip()
        if not content:
            return "Your clipboard is empty, nothing to summarize."

        if ai_brain:
            summary = ai_brain.ask(
                f"Please summarize this text concisely: {content}"
            )
            return summary
        else:
            # Basic fallback if no AI brain available
            words = content.split()
            if len(words) <= 20:
                return f"Clipboard content: {content}"
            return f"Clipboard has {len(words)} words starting with: {' '.join(words[:20])}..."
    except Exception as e:
        return f"Could not read clipboard: {e}"
