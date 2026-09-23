from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.models import AlertLogModel
from app.protocol import DeviceStatus, Severity
from app.widgets.stat_card import StatCard
from app.widgets.status_hero import StatusHero
from app.widgets.timeline import IntegrityTimeline


class DashboardPage(QWidget):
    """
    Professional-grade telemetry command & control center styled with a high-end
    dark aesthetic, high-contrast metrics, rolling integrity chart, and a structured
    bottom action/navigation footer reflecting active connection or simulation state.
    """

    navigate_requested = Signal(str)  # Signal to request navigation to other pages (e.g., 'log')

    def __init__(self, log_model: AlertLogModel, parent=None):
        super().__init__(parent)
        self._log_model = log_model
        self._total_checks = 0
        self._critical_count = 0
        self._session_start: datetime | None = None
        self._device_status: DeviceStatus | None = None
        self._connected_port: str = ""
        self._connected_baud: int = 115200

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Header Section ───────────────────────────────────────────────────
        header_card = QFrame()
        header_card.setObjectName("headerCard")
        header_card.setStyleSheet("""
            QFrame#headerCard {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-left: 4px solid #38BDF8;
                border-radius: 10px;
            }
        """)
        header_lay = QVBoxLayout(header_card)
        header_lay.setContentsMargins(24, 20, 24, 20)
        header_lay.setSpacing(6)

        title = QLabel("Telemetry Command & Control")
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 20px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel("Live runtime firmware integrity metrics and telemetry stream for connected ESP32 hardware or simulation.")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setStyleSheet("""
            color: #94A3B8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            background: transparent;
            border: none;
        """)

        header_lay.addWidget(title)
        header_lay.addWidget(subtitle)
        root.addWidget(header_card)

        # ── Hero Status Banner ───────────────────────────────────────────────
        self.hero = StatusHero()
        root.addWidget(self.hero)

        # ── Metrics Statistic Cards Row ──────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.card_checks = StatCard("Total Checks", "0")
        self.card_alerts = StatCard("Critical Alerts", "0")
        self.card_uptime = StatCard("Session Uptime", "00:00:00")
        self.card_firmware = StatCard("Firmware Version", "–")
        for card in (self.card_checks, self.card_alerts, self.card_uptime, self.card_firmware):
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── Integrity Timeline Chart ─────────────────────────────────────────
        self.timeline = IntegrityTimeline()
        root.addWidget(self.timeline)

        # ── Recent Events Table Section ──────────────────────────────────────
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(20, 20, 20, 20)
        tc_layout.setSpacing(12)

        recent_label = QLabel("RECENT SECURITY EVENTS")
        recent_label.setObjectName("cardTitle")
        recent_label.setStyleSheet("""
            color: #94A3B8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            background: transparent;
            border: none;
        """)
        tc_layout.addWidget(recent_label)

        self.recent_table = QTableView()
        self.recent_table.setModel(log_model)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setSelectionBehavior(QTableView.SelectRows)
        self.recent_table.setEditTriggers(QTableView.NoEditTriggers)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setMinimumHeight(140)
        
        header = self.recent_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #1E293B;
                color: #F8FAFC;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 700;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #334155;
                border-right: 1px solid #0B0F19;
            }
        """)
        
        self.recent_table.setStyleSheet("""
            QTableView {
                background-color: #070A10;
                alternate-background-color: #0B0F19;
                color: #F8FAFC;
                gridline-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
            }
            QTableView::item {
                padding: 6px 8px;
                border: none;
            }
            QTableView::item:selected {
                background-color: #1E293B;
                color: #38BDF8;
            }
        """)
        
        tc_layout.addWidget(self.recent_table)
        root.addWidget(table_container, 1)

        # ── Professional Bottom Action & Navigation Footer ───────────────────
        footer_card = QFrame()
        footer_card.setStyleSheet("""
            QFrame {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }
        """)
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(20, 14, 20, 14)

        self.footer_info = QLabel("Disconnected — No Active Telemetry Feed")
        self.footer_info.setStyleSheet("""
            color: #38BDF8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)

        view_log_btn = QPushButton("View Complete Alert Log →")
        view_log_btn.setCursor(Qt.PointingHandCursor)
        view_log_btn.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #334155;
                border-color: #38BDF8;
                color: #38BDF8;
            }
        """)
        view_log_btn.clicked.connect(lambda: self.navigate_requested.emit("log"))

        footer_layout.addWidget(self.footer_info)
        footer_layout.addStretch(1)
        footer_layout.addWidget(view_log_btn)
        
        root.addWidget(footer_card)

    # ------------------------------------------------------------------
    def on_connected(self, port: str = "", baud: int = 115200) -> None:
        self._session_start = datetime.now()
        self._connected_port = port
        self._connected_baud = baud

        if port == "__SIMULATE__":
            self.footer_info.setText("Simulation Mode Active — Generating Synthetic Telemetry")
            self.hero.set_severity(Severity.UNKNOWN, "Simulation Mode Active - waiting for initial telemetry frame.")
        else:
            port_str = f"{port} @ {baud} baud" if port else "Serial UART"
            self.footer_info.setText(f"Secure UART Telemetry Feed Active on {port_str}")
            self.hero.set_severity(Severity.UNKNOWN, "Connected - waiting for the first status frame.")

    def on_disconnected(self, reason: str) -> None:
        self._session_start = None
        self._device_status = None
        self._connected_port = ""
        self.footer_info.setText("Disconnected — No Active Telemetry Feed")
        self.hero.set_severity(Severity.UNKNOWN, reason or "Disconnected.")
        self.hero.set_device_info("")

    def on_status(self, status: DeviceStatus) -> None:
        self._device_status = status
        self.card_firmware.set_value(status.fw_version)
        mode_prefix = "[Simulated] " if self._connected_port == "__SIMULATE__" else ""
        self.hero.set_device_info(f"{mode_prefix}{status.hardware_revision}\nfw {status.fw_version}")

    def on_alert(self, event) -> None:
        self._total_checks += 1
        if event.severity == Severity.CRITICAL:
            self._critical_count += 1

        self.card_checks.set_value(str(self._total_checks))
        self.card_alerts.set_value(str(self._critical_count))
        self.timeline.add_point(event.severity)

        detail = f"Last event: {event.event_code} @ {event.received_at.strftime('%H:%M:%S')}"
        self.hero.set_severity(event.severity, detail)
        self.recent_table.scrollToBottom()

    def tick_uptime(self) -> None:
        if self._session_start is None:
            return
        elapsed = datetime.now() - self._session_start
        total_seconds = int(elapsed.total_seconds())
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        self.card_uptime.set_value(f"{h:02d}:{m:02d}:{s:02d}")

    def reset_session_stats(self) -> None:
        self._total_checks = 0
        self._critical_count = 0
        self.card_checks.set_value("0")
        self.card_alerts.set_value("0")
        self.timeline.clear()