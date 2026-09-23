from __future__ import annotations

from PySide6.QtCore import Property, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.protocol import Severity

_STATE_TEXT = {
    Severity.INFO: ("SYSTEM SECURE", "statusHeroSafe", QColor("#22C55E")),
    Severity.WARNING: ("ATTENTION REQUIRED", "statusHeroWarning", QColor("#F59E0B")),
    Severity.CRITICAL: ("INTEGRITY VIOLATION", "statusHeroCritical", QColor("#EF4444")),
    Severity.UNKNOWN: ("AWAITING DEVICE", "statusHeroUnknown", QColor("#94A3B8")),
}


class _PulseDot(QWidget):
    """A soft-glowing circular status indicator that breathes continuously."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self._color = QColor("#94A3B8")
        self._radius = 4.0

        self._anim = QPropertyAnimation(self, b"radius", self)
        self._anim.setDuration(1100)
        self._anim.setStartValue(3.5)
        self._anim.setEndValue(5.5)
        self._anim.setLoopCount(1)
        self._anim.finished.connect(self._reverse_direction)
        self._anim.start()

    def _reverse_direction(self) -> None:
        new_dir = (
            QPropertyAnimation.Backward
            if self._anim.direction() == QPropertyAnimation.Forward
            else QPropertyAnimation.Forward
        )
        self._anim.setDirection(new_dir)
        self._anim.start()

    def get_radius(self) -> float:
        return self._radius

    def set_radius(self, value: float) -> None:
        self._radius = value
        self.update()

    radius = Property(float, get_radius, set_radius)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()

        glow = QColor(self._color)
        glow.setAlpha(60)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, self._radius + 4, self._radius + 4)

        painter.setBrush(self._color)
        painter.drawEllipse(center, self._radius, self._radius)


class StatusHero(QFrame):
    """
    Professional headline status banner featuring real-time device health states,
    pulsing telemetry indicators, and hardware connection context.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Directly apply background & border inline to avoid objectName collisions
        self.setStyleSheet("""
            StatusHero {
                background-color: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        self.setMinimumHeight(120)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(18)

        self._dot = _PulseDot(self)
        outer.addWidget(self._dot, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        self._headline = QLabel(_STATE_TEXT[Severity.UNKNOWN][0])
        self._headline.setStyleSheet("""
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 18px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        self._detail = QLabel("No device connected yet.")
        self._detail.setStyleSheet("""
            color: #94A3B8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            background: transparent;
            border: none;
        """)

        text_col.addWidget(self._headline)
        text_col.addWidget(self._detail)
        outer.addLayout(text_col, 1)

        self._device_label = QLabel("")
        self._device_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._device_label.setStyleSheet("""
            color: #94A3B8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        outer.addWidget(self._device_label, 0, Qt.AlignTop)

    def paintEvent(self, event):  # noqa: N802
        # Ensures custom QFrame subclasses properly render stylesheets in Qt
        from PySide6.QtWidgets import QStyle, QStyleOption
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def set_severity(self, severity: Severity, detail: str) -> None:
        text, _, color = _STATE_TEXT[severity]
        self._headline.setText(text)
        self._detail.setText(detail)
        self._dot.set_color(color)

    def set_device_info(self, text: str) -> None:
        self._device_label.setText(text)