"""
Wednesday AI Assistant — GUI Components
OrbWidget, StatusLabel, ChatPanel, InputBar, SidePanel, ToggleSwitch.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
    QFrame,
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtProperty, QPointF, QRectF, QTimer, QSize,
    QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QRadialGradient, QFont, QPainterPath,
)

from gui.theme import Colors, STATE_QCOLORS, STATE_HEX, STATUS_TEXT


# ═════════════════════════════════════════════════════════════════
#  1. AI ORB — Central animated sphere with rotating rings
# ═════════════════════════════════════════════════════════════════

class OrbWidget(QWidget):
    """
    Custom-painted AI orb with layered gradients, rotating arc rings,
    and orbiting particles.  Exposes animated properties that are
    driven by OrbAnimator (see animations.py).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        # Animated property backing fields
        self._scale_factor: float = 1.0
        self._rotation_angle: float = 0.0
        self._glow_intensity: float = 0.7
        self._state_color: QColor = STATE_QCOLORS["idle"]

    # ── pyqtProperty declarations (for QPropertyAnimation) ──────

    @pyqtProperty(float)
    def scaleFactor(self):
        return self._scale_factor

    @scaleFactor.setter
    def scaleFactor(self, v):
        self._scale_factor = v
        self.update()

    @pyqtProperty(float)
    def rotationAngle(self):
        return self._rotation_angle

    @rotationAngle.setter
    def rotationAngle(self, v):
        self._rotation_angle = v
        self.update()

    @pyqtProperty(float)
    def glowIntensity(self):
        return self._glow_intensity

    @glowIntensity.setter
    def glowIntensity(self, v):
        self._glow_intensity = v
        self.update()

    # ── state management ─────────────────────────────────────────

    def set_state_color(self, state: str):
        self._state_color = STATE_QCOLORS.get(state, STATE_QCOLORS["idle"])
        self.update()

    def set_custom_color(self, color: QColor):
        """Used by the transition manager to apply intermediate colors."""
        self._state_color = color
        self.update()

    # ── painting ─────────────────────────────────────────────────

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base = min(w, h) * 0.35
        s = self._scale_factor
        gi = self._glow_intensity
        r, g, b = (self._state_color.red(),
                    self._state_color.green(),
                    self._state_color.blue())

        painter.translate(cx, cy)

        # ── L1: ambient glow ──
        amb = QRadialGradient(0, 0, base * 1.8)
        amb.setColorAt(0.0, QColor(r, g, b, int(18 * gi)))
        amb.setColorAt(0.5, QColor(r, g, b, int(6 * gi)))
        amb.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(amb))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), base * 1.8, base * 1.8)

        # ── L2: outer rotating arcs ──
        painter.save()
        painter.rotate(self._rotation_angle)
        pen1 = QPen(QColor(r, g, b, int(120 * gi)))
        pen1.setWidthF(2.0)
        painter.setPen(pen1)
        rr1 = base * 1.2 * s
        rect1 = QRectF(-rr1, -rr1, rr1 * 2, rr1 * 2)
        for i in range(8):
            painter.drawArc(rect1, i * 45 * 16, 28 * 16)
        painter.restore()

        # ── L3: inner counter-rotating arcs ──
        painter.save()
        painter.rotate(-self._rotation_angle * 0.65)
        pen2 = QPen(QColor(r, g, b, int(75 * gi)))
        pen2.setWidthF(1.5)
        painter.setPen(pen2)
        rr2 = base * 1.05 * s
        rect2 = QRectF(-rr2, -rr2, rr2 * 2, rr2 * 2)
        for i in range(6):
            painter.drawArc(rect2, (i * 60 + 15) * 16, 35 * 16)
        painter.restore()

        # ── L4: sphere glow ──
        sr_ = base * 0.82 * s
        glow = QRadialGradient(0, 0, sr_)
        glow.setColorAt(0.0, QColor(r, g, b, int(170 * gi)))
        glow.setColorAt(0.3, QColor(r, g, b, int(90 * gi)))
        glow.setColorAt(0.7, QColor(r, g, b, int(25 * gi)))
        glow.setColorAt(1.0, QColor(r, g, b, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), sr_, sr_)

        # ── L5: bright core ──
        cr = base * 0.24 * s
        core = QRadialGradient(0, 0, cr)
        core.setColorAt(0.0, QColor(255, 255, 255, int(210 * gi)))
        core.setColorAt(0.5, QColor(r, g, b, int(170 * gi)))
        core.setColorAt(1.0, QColor(r, g, b, int(40 * gi)))
        painter.setBrush(QBrush(core))
        painter.drawEllipse(QPointF(0, 0), cr, cr)

        # ── L6: center dot ──
        dr = base * 0.055
        painter.setBrush(QColor(255, 255, 255, int(230 * gi)))
        painter.drawEllipse(QPointF(0, 0), dr, dr)

        # ── L7: orbiting particles ──
        painter.save()
        painter.rotate(self._rotation_angle * 1.4)
        for i in range(12):
            pr = base * (0.88 + 0.18 * ((i * 7 + 3) % 5) / 5) * s
            painter.setBrush(QColor(r, g, b, int(140 * gi)))
            painter.save()
            painter.rotate(i * 30)
            size = 1.5 + (i % 3) * 0.5
            painter.drawEllipse(QPointF(pr, 0), size, size)
            painter.restore()
        painter.restore()

        painter.end()


# ═════════════════════════════════════════════════════════════════
#  2. STATUS LABEL — animated text below orb
# ═════════════════════════════════════════════════════════════════

class StatusLabel(QLabel):
    """Futuristic status text with fade transitions on state change."""

    def __init__(self, parent=None):
        super().__init__("Idle", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        self._current_state = "idle"
        self._apply_style("idle")

    def set_state(self, state: str):
        if state == self._current_state:
            return
        self._current_state = state
        self.setText(STATUS_TEXT.get(state, "Idle"))
        self._apply_style(state)

    def _apply_style(self, state: str):
        color = STATE_HEX.get(state, "#666666")
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 14px;
                letter-spacing: 3px;
                text-transform: uppercase;
                padding: 6px;
            }}
        """)


# ═════════════════════════════════════════════════════════════════
#  3. CHAT PANEL — conversation history with styled bubbles
# ═════════════════════════════════════════════════════════════════

class ChatBubble(QFrame):
    """Single chat message bubble."""

    def __init__(self, role: str, text: str, parent=None):
        super().__init__(parent)
        is_user = (role == "user")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # Role label
        role_lbl = QLabel("You" if is_user else "Wednesday")
        role_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        role_lbl.setStyleSheet(
            f"color: {Colors.BLUE if is_user else Colors.PURPLE};"
            " padding: 0; margin: 0;"
        )

        # Text
        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setFont(QFont("Segoe UI", 12))
        msg_lbl.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; padding: 0; margin: 0;"
        )

        layout.addWidget(role_lbl)
        layout.addWidget(msg_lbl)

        # Bubble style
        accent = Colors.BLUE if is_user else Colors.PURPLE
        self.setStyleSheet(f"""
            ChatBubble {{
                background-color: {Colors.BG_TERTIARY};
                border: 1px solid {accent}33;
                border-radius: 14px;
                border-{'right' if is_user else 'left'}: 3px solid {accent};
            }}
        """)
        self.setMaximumWidth(520)


class ChatPanel(QScrollArea):
    """Scrollable conversation history panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(10)
        self._layout.addStretch()
        self.setWidget(self._container)

        self.setStyleSheet(f"""
            QScrollArea {{ background: {Colors.BG_PRIMARY}; }}
            QWidget {{ background: transparent; }}
        """)

    def add_message(self, role: str, text: str):
        bubble = ChatBubble(role, text)

        # Alignment
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if role == "user":
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        w = QWidget()
        w.setLayout(wrapper)
        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, w)

        # Auto-scroll to bottom
        QTimer.singleShot(50, self._scroll_bottom)

    def _scroll_bottom(self):
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


# ═════════════════════════════════════════════════════════════════
#  4. INPUT BAR — text field + send button
# ═════════════════════════════════════════════════════════════════

class InputBar(QWidget):
    """Text input with send button. Emits command_submitted(str)."""

    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command…")
        self._input.setMinimumHeight(44)
        self._input.returnPressed.connect(self._send)

        self._btn = QPushButton("➤")
        self._btn.setFixedSize(44, 44)
        self._btn.setFont(QFont("Segoe UI", 16))
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._send)
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BLUE};
                color: {Colors.BG_PRIMARY};
                border: none;
                border-radius: 22px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #33e0ff;
                color: {Colors.BG_PRIMARY};
            }}
        """)

        layout.addWidget(self._input)
        layout.addWidget(self._btn)

    def _send(self):
        text = self._input.text().strip()
        if text:
            self.command_submitted.emit(text)
            self._input.clear()

    def set_enabled(self, enabled: bool):
        self._input.setEnabled(enabled)
        self._btn.setEnabled(enabled)


# ═════════════════════════════════════════════════════════════════
#  5. TOGGLE SWITCH — custom painted ON/OFF
# ═════════════════════════════════════════════════════════════════

class ToggleSwitch(QWidget):
    """Animated toggle switch."""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._circle_x = 4

        self._anim = QPropertyAnimation(self, b"circleX")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @pyqtProperty(int)
    def circleX(self):
        return self._circle_x

    @circleX.setter
    def circleX(self, v):
        self._circle_x = v
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, val: bool):
        self._checked = val
        self._anim.setStartValue(self._circle_x)
        self._anim.setEndValue(24 if val else 4)
        self._anim.start()
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._anim.setStartValue(self._circle_x)
        self._anim.setEndValue(24 if self._checked else 4)
        self._anim.start()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_col = QColor(Colors.BLUE) if self._checked else QColor(Colors.BG_TERTIARY)
        track_col.setAlpha(100 if self._checked else 180)
        p.setBrush(track_col)
        p.setPen(QPen(QColor(Colors.BORDER_LIGHT), 1))
        p.drawRoundedRect(0, 0, 46, 24, 12, 12)

        thumb = QColor(Colors.BLUE) if self._checked else QColor(Colors.TEXT_MUTED)
        p.setBrush(thumb)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self._circle_x, 3, 18, 18)
        p.end()


# ═════════════════════════════════════════════════════════════════
#  6. SIDE PANEL — toggles + system info
# ═════════════════════════════════════════════════════════════════

class SidePanel(QWidget):
    """Control panel with toggle switches."""

    voice_toggled   = pyqtSignal(bool)
    gesture_toggled = pyqtSignal(bool)
    safe_toggled    = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"""
            SidePanel {{
                background-color: {Colors.BG_SECONDARY};
                border-left: 1px solid {Colors.BORDER};
                border-radius: 0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        # Title
        title = QLabel("CONTROLS")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; letter-spacing: 3px;"
        )
        layout.addWidget(title)
        layout.addSpacing(14)

        # Toggles
        self.voice_toggle = self._add_toggle(layout, "Voice Input", False)
        self.gesture_toggle = self._add_toggle(layout, "Gesture Control", False)
        self.safe_toggle = self._add_toggle(layout, "Safe Mode", True)

        self.voice_toggle.toggled.connect(self.voice_toggled)
        self.gesture_toggle.toggled.connect(self.gesture_toggled)
        self.safe_toggle.toggled.connect(self.safe_toggled)

        layout.addSpacing(24)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {Colors.BORDER};")
        layout.addWidget(div)
        layout.addSpacing(14)

        # System info section
        info_title = QLabel("SYSTEM")
        info_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        info_title.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; letter-spacing: 3px;"
        )
        layout.addWidget(info_title)
        layout.addSpacing(8)

        self.status_label = QLabel("Status: Online")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet(f"color: {Colors.GREEN};")
        layout.addWidget(self.status_label)

        self.thread_label = QLabel("Threads: 0")
        self.thread_label.setFont(QFont("Segoe UI", 11))
        self.thread_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.thread_label)

        layout.addStretch()

    def _add_toggle(self, layout, label: str, default: bool) -> ToggleSwitch:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        toggle = ToggleSwitch()
        toggle.setChecked(default)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(toggle)
        w = QWidget()
        w.setLayout(row)
        w.setFixedHeight(36)
        layout.addWidget(w)
        return toggle
