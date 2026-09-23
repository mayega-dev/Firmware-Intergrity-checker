from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QStyle, QStyleOption


class StatCard(QFrame):
    """A clean, professional metric tile showcasing key indicators and numerical telemetry."""

    def __init__(self, title: str, value: str = "--", parent=None):
        super().__init__(parent)
        # Directly apply background & border inline
        self.setStyleSheet("""
            StatCard {
                background-color: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(88)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self._title_label = QLabel(title.upper())
        self._title_label.setStyleSheet("""
            color: #94A3B8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet("""
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 22px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)
        layout.addStretch(1)

    def paintEvent(self, event):  # noqa: N802
        # Ensures custom QFrame subclasses properly render stylesheets in Qt
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)