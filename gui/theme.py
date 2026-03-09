"""
Wednesday - GUI Theme
Design tokens and stylesheet for the assistant window.
"""

# Color palette
COLORS = {
    "bg_dark": "#0d0d1a",
    "bg_panel": "#131328",
    "bg_card": "#1a1a3e",
    "bg_input": "#0f0f25",
    "accent": "#7c3aed",
    "accent_light": "#a78bfa",
    "accent_glow": "#8b5cf6",
    "text_primary": "#f0f0ff",
    "text_secondary": "#8888aa",
    "text_muted": "#555577",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "border": "#252548",
    "border_focus": "#7c3aed",
    "sleeping": "#6b7280",
    "listening": "#3b82f6",
    "thinking": "#8b5cf6",
    "speaking": "#22c55e",
    "user_msg": "#a78bfa",
    "assistant_msg": "#22c55e",
}

FONT_FAMILY = "Segoe UI"

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: 18px;
}}
QWidget#centralWidget {{
    background-color: {COLORS['bg_dark']};
    border-radius: 18px;
}}
QLabel#titleLabel {{
    color: {COLORS['accent_light']};
    font-family: {FONT_FAMILY};
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QLabel#statusLabel {{
    color: {COLORS['text_secondary']};
    font-family: {FONT_FAMILY};
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
}}
QTextEdit#chatHistory {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 12px;
    font-family: {FONT_FAMILY};
    font-size: 13px;
    selection-background-color: {COLORS['accent']};
}}
QTextEdit#chatHistory QScrollBar:vertical {{
    background: {COLORS['bg_panel']};
    width: 6px;
    border-radius: 3px;
    margin: 4px 2px;
}}
QTextEdit#chatHistory QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 3px;
    min-height: 30px;
}}
QTextEdit#chatHistory QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent']};
}}
QTextEdit#chatHistory QScrollBar::add-line:vertical,
QTextEdit#chatHistory QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QLineEdit#inputField {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px 14px;
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QLineEdit#inputField:focus {{
    border: 1px solid {COLORS['border_focus']};
}}
QPushButton#micButton {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton#micButton:hover {{
    background-color: {COLORS['accent']};
    color: white;
    border-color: {COLORS['accent']};
}}
QPushButton#micButton:pressed {{
    background-color: {COLORS['accent_light']};
}}
QPushButton#sendButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton#sendButton:hover {{
    background-color: {COLORS['accent_light']};
}}
QPushButton#sendButton:pressed {{
    background-color: {COLORS['accent_glow']};
}}
QPushButton#closeButton {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: none;
    font-size: 16px;
    font-weight: bold;
    min-width: 30px;
    min-height: 30px;
    border-radius: 15px;
}}
QPushButton#closeButton:hover {{
    color: {COLORS['error']};
    background-color: rgba(239, 68, 68, 30);
}}
"""
