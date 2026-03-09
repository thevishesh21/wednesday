"""
Wednesday - Screen Awareness Skill
Captures a screenshot and uses OpenAI Vision to describe what is on screen.
"""

import base64
import io
import logging

from openai import OpenAI
import config

logger = logging.getLogger("Wednesday")


def _capture_screenshot() -> bytes:
    """Capture the primary monitor and return PNG bytes."""
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            img = sct.grab(monitor)
            png = mss.tools.to_png(img.rgb, img.size)
            return png
    except ImportError:
        pass

    # Fallback to pyautogui
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        buf = io.BytesIO()
        screenshot.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("Install mss or pyautogui for screen capture.")


def analyze_screen(prompt: str = "Describe what is on the screen.") -> str:
    """Capture a screenshot and send it to OpenAI Vision for analysis."""
    try:
        png_bytes = _capture_screenshot()
    except Exception as e:
        return f"Could not capture screenshot: {e}"

    b64_image = base64.b64encode(png_bytes).decode("utf-8")

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=config.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are Wednesday, an AI desktop assistant. "
                                "The user asked you to look at their screen. "
                                f"User request: {prompt}\n"
                                "Describe what you see concisely in 1-3 sentences. "
                                "Speak naturally as a voice assistant would."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[ScreenAwareness] Vision API error: %s", e)
        return f"Sorry, I could not analyze the screen: {e}"
