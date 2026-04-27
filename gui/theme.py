"""
Wednesday AI Assistant — GUI Theme
Futuristic JARVIS-style dark theme with neon accents.
"""

from PyQt6.QtGui import QColor


# ═════════════════════════════════════════════════════════════════
#  Color Palette
# ═════════════════════════════════════════════════════════════════

class Colors:
    """Central color constants for the JARVIS theme."""

    # Backgrounds
    BG_PRIMARY   = "#0a0a0a"
    BG_SECONDARY = "#0f0f0f"
    BG_TERTIARY  = "#161616"
    BG_CARD      = "#1a1a1a"
    BG_INPUT     = "#0e0e0e"
    BG_HOVER     = "#1e1e1e"
    BG_TITLE     = "#070707"

    # Accents
    BLUE   = "#00d4ff"
    PURPLE = "#8a2be2"
    GREEN  = "#00ff88"
    RED    = "#ff4757"

    # Text
    TEXT_PRIMARY   = "#d4d4d4"
    TEXT_SECONDARY = "#777777"
    TEXT_MUTED     = "#444444"
    TEXT_BRIGHT    = "#ffffff"

    # Borders
    BORDER       = "#1c1c1c"
    BORDER_LIGHT = "#2a2a2a"


# ═════════════════════════════════════════════════════════════════
#  State Colors (for the AI Orb)
# ═════════════════════════════════════════════════════════════════

STATE_QCOLORS = {
    "idle":      QColor(100, 100, 100),
    "listening": QColor(0, 212, 255),
    "thinking":  QColor(138, 43, 226),
    "speaking":  QColor(0, 255, 136),
    "executing": QColor(255, 191, 0),
    "error":     QColor(255, 107, 107),
    "complete":  QColor(0, 255, 255),
}

STATE_HEX = {
    "idle":      "#666666",
    "listening": "#00d4ff",
    "thinking":  "#8a2be2",
    "speaking":  "#00ff88",
    "executing": "#ffbf00",
    "error":     "#ff6b6b",
    "complete":  "#00ffff",
}

STATUS_TEXT = {
    "idle":      "Idle",
    "listening": "Listening…",
    "thinking":  "Thinking…",
    "speaking":  "Speaking…",
    "executing": "Executing…",
    "error":     "Error!",
    "complete":  "Complete",
}


# ═════════════════════════════════════════════════════════════════
#  Global QSS Stylesheet
# ═════════════════════════════════════════════════════════════════

MAIN_STYLESHEET = f"""
/* ── Window ──────────────────────────────────────────── */
QMainWindow {{
    background-color: {Colors.BG_PRIMARY};
}}
QWidget#centralWidget {{
    background-color: {Colors.BG_PRIMARY};
}}
QWidget {{
    color: {Colors.TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

/* ── Scroll ──────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {Colors.BG_SECONDARY};
    width: 5px;
    border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BORDER_LIGHT};
    border-radius: 2px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0; background: none;
}}

/* ── Input ───────────────────────────────────────────── */
QLineEdit {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 10px 18px;
    font-size: 14px;
    selection-background-color: {Colors.BLUE};
}}
QLineEdit:focus {{
    border-color: {Colors.BLUE};
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {Colors.BG_HOVER};
    border-color: {Colors.BLUE};
    color: {Colors.BLUE};
}}
QPushButton:pressed {{
    background-color: {Colors.BG_PRIMARY};
}}
QLabel {{
    background: transparent;
}}
"""
