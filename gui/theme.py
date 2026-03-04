"""
Wednesday - GUI Theme
Design tokens and stylesheet for the assistant window.
"""

# Color palette
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_panel": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "accent_light": "#ff6b81",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "sleeping": "#5a6078",
    "listening": "#3498db",
    "thinking": "#f39c12",
    "speaking": "#2ecc71",
}

FONT_FAMILY = "Segoe UI"

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['bg_card']};
    border-radius: 16px;
}}
QWidget#centralWidget {{
    background-color: {COLORS['bg_dark']};
    border-radius: 16px;
}}
QLabel#titleLabel {{
    color: {COLORS['text_primary']};
    font-family: {FONT_FAMILY};
    font-size: 18px;
    font-weight: bold;
}}
QLabel#statusLabel {{
    color: {COLORS['text_secondary']};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QLabel#transcriptLabel {{
    color: {COLORS['text_primary']};
    font-family: {FONT_FAMILY};
    font-size: 12px;
    padding: 8px;
}}
QLabel#responseLabel {{
    color: {COLORS['accent_light']};
    font-family: {FONT_FAMILY};
    font-size: 12px;
    padding: 8px;
}}
QPushButton#micButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 14px;
    font-weight: bold;
    min-width: 50px;
    min-height: 50px;
}}
QPushButton#micButton:hover {{
    background-color: {COLORS['accent_light']};
}}
QPushButton#micButton:pressed {{
    background-color: #c0392b;
}}
QPushButton#closeButton {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    font-size: 16px;
    font-weight: bold;
    min-width: 30px;
    min-height: 30px;
}}
QPushButton#closeButton:hover {{
    color: {COLORS['accent']};
}}
"""
