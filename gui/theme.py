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
QTextEdit#chatHistory {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['bg_card']};
    border-radius: 8px;
    padding: 10px;
    font-family: {FONT_FAMILY};
    font-size: 12px;
}}
QLineEdit#inputField {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['bg_card']};
    border-radius: 8px;
    padding: 8px 12px;
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QLineEdit#inputField:focus {{
    border: 1px solid {COLORS['accent']};
}}
QPushButton#micButton {{
    background-color: {COLORS['bg_card']};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton#micButton:hover {{
    background-color: {COLORS['accent']};
}}
QPushButton#micButton:pressed {{
    background-color: #c0392b;
}}
QPushButton#sendButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton#sendButton:hover {{
    background-color: {COLORS['accent_light']};
}}
QPushButton#sendButton:pressed {{
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
