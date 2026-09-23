from __future__ import annotations

from collections import deque

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QLabel

from app.protocol import Severity
from app.models import SEVERITY_COLORS


class IntegrityTimeline(QFrame):
    """
    A professional rolling strip chart providing a visual timeline of received
    events colored by severity, allowing operators to spot status patterns at a glance.
    """

    def __init__(self, max_points: int = 120, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        self._max_points = max_points
        self._points: deque[Severity] = deque(maxlen=max_points)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        
        title = QLabel("INTEGRITY CHECK TIMELINE")
        title.setObjectName("cardTitle")
        title.setStyleSheet("""
            color: #94A3B8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)
        layout.addStretch(1)
        self._plot_margin_top = 36

    def add_point(self, severity: Severity) -> None:
        self._points.append(severity)
        self.update()

    def clear(self) -> None:
        self._points.clear()
        self.update()

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(
            24,
            self._plot_margin_top,
            self.width() - 48,
            self.height() - self._plot_margin_top - 20,
        )

        # Technical Grid Lines / Reference Ticks
        painter.setPen(QPen(QColor("#1E293B"), 1, Qt.DashLine))
        mid_y = rect.top() + (rect.height() * 0.5)
        painter.drawLine(rect.left(), mid_y, rect.right(), mid_y)

        # High-contrast Professional Baseline
        painter.setPen(QPen(QColor("#334155"), 1.5))
        baseline_y = rect.bottom()
        painter.drawLine(rect.left(), baseline_y, rect.right(), baseline_y)

        if not self._points:
            painter.setPen(QColor("#64748B"))
            painter.setFont(painter.font())
            painter.drawText(rect, Qt.AlignCenter, "Waiting for telemetry data stream…")
            return

        n = len(self._points)
        slot_w = rect.width() / self._max_points
        bar_w = max(2.5, slot_w * 0.65)
        offset = self._max_points - n

        for i, severity in enumerate(self._points):
            base_color = SEVERITY_COLORS.get(severity, QColor("#64748B"))
            
            x = rect.left() + (offset + i) * slot_w
            # Scale amplitude cleanly depending on severity
            if severity == Severity.CRITICAL:
                height = rect.height()
            elif severity == Severity.WARNING:
                height = rect.height() * 0.55
            else:
                height = rect.height() * 0.30

            bar_rect = QRectF(x, rect.bottom() - height, bar_w, height)

            # Professional Gradient Shading for Signals
            gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
            gradient.setColorAt(0.0, base_color.lighter(120))
            gradient.setColorAt(1.0, base_color)

            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_rect, 2.0, 2.0)