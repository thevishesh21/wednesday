"""
Wednesday AI Assistant — OCR Module
Extracts text from the screen using pytesseract.
"""

from utils.logger import get_logger
from vision.screenshot import get_screenshot_image
import config

log = get_logger("ocr")

# ── Configure Tesseract path ────────────────────────────────────
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    _ocr_available = True
    log.info("Tesseract OCR configured.")
except ImportError:
    _ocr_available = False
    log.warning("pytesseract not installed — OCR unavailable.")


def read_screen_text() -> str:
    """
    Take a screenshot and extract all visible text via OCR.

    Returns:
        Extracted text string, or error message.
    """
    if not _ocr_available:
        return "OCR is not available. Please install pytesseract and Tesseract."

    log.info("Reading screen text via OCR...")
    try:
        img = get_screenshot_image()
        if img is None:
            return "Screenshot failed — cannot read screen."

        text = pytesseract.image_to_string(img).strip()
        if text:
            log.info(f"OCR extracted {len(text)} characters.")
            return text[:500]  # Limit for spoken output
        else:
            return "Screen par koi readable text nahi mila, boss."

    except Exception as e:
        log.error(f"OCR failed: {e}")
        return f"OCR error: {e}"


def is_ocr_available() -> bool:
    """Check if Tesseract OCR is available."""
    return _ocr_available
