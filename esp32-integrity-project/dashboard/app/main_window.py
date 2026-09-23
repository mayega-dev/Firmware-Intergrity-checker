from __future__ import annotations

from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QVBoxLayout, 
    QMainWindow, 
    QStackedWidget, 
    QWidget, 
    QScrollArea
)

from app.device_link import DeviceLink, SerialLink, SimulatorLink
from app.models import AlertLogModel
from app.protocol import AlertEvent, DeviceStatus, Severity
from app.widgets.console_page import ConsolePage
from app.widgets.dashboard_page import DashboardPage
from app.widgets.docs_page import DocumentationPage
from app.widgets.log_page import LogPage
from app.widgets.settings_page import SettingsPage
from app.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    """
    Professional main application window managing device telemetry threads,
    stacked views wrapped in smooth scroll areas, and a bottom navigation layout footer.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firmware Integrity Monitor")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)

        self._link: DeviceLink | None = None
        self._log_model = AlertLogModel(self)

        # Global application stylesheet establishing a high-end engineering look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #070A10;
                color: #F8FAFC;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0B0F19;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #1E293B;
                min-height: 25px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #070A10;")
        layout.addWidget(self.stack, 1)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        layout.addWidget(self.sidebar)

        # Initialize pages
        self.dashboard_page = DashboardPage(self._log_model)
        self.dashboard_page.navigate_requested.connect(self._switch_page)

        self.log_page = LogPage(self._log_model)
        self.console_page = ConsolePage()
        self.settings_page = SettingsPage()
        self.docs_page = DocumentationPage()

        self._dashboard_scroll = QScrollArea()
        self._dashboard_scroll.setWidgetResizable(True)
        self._dashboard_scroll.setWidget(self.dashboard_page)
        self._dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._pages = {
            "dashboard": self._dashboard_scroll,
            "log": self.log_page,
            "console": self.console_page,
            "settings": self.settings_page,
            "docs": self.docs_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self._dashboard_scroll)

        self.settings_page.connect_requested.connect(self._start_link)
        self.settings_page.disconnect_requested.connect(self._stop_link)
        self.console_page.command_requested.connect(self._send_command)

        self._uptime_timer = QTimer(self)
        self._uptime_timer.setInterval(1000)
        self._uptime_timer.timeout.connect(self.dashboard_page.tick_uptime)
        self._uptime_timer.start()

    def _switch_page(self, key: str) -> None:
        page = self._pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)
            self.sidebar.set_active(key)

    def _start_link(self, port: str, baud: int) -> None:
        if self._link is not None:
            self._stop_link()

        if port == "__SIMULATE__":
            self._link = SimulatorLink()
            self.console_page.append_line("[INFO] Starting telemetry in SIMULATION mode.")
        else:
            self._link = SerialLink(port, baud)
            self.console_page.append_line(f"[INFO] Opening real hardware serial port {port} at {baud} baud...")

        self._link.connected.connect(self._on_connected)
        self._link.disconnected.connect(self._on_disconnected)
        self._link.status_received.connect(self._on_status)
        self._link.alert_received.connect(self._on_alert)
        self._link.raw_line_received.connect(self._handle_raw_line)
        self._link.link_error.connect(self._on_link_error)
        self._link.start()

        self.settings_page.set_connected_ui_state(True)

    def _stop_link(self) -> None:
        if self._link is not None:
            self._link.stop()
            self._link.wait(1500)
            self._link = None
        self.settings_page.set_connected_ui_state(False)
        self.sidebar.set_connection_state("disconnected")
        self.dashboard_page.on_disconnected("Disconnected.")

    def _send_command(self, command: str) -> None:
        if self._link is not None:
            self._link.send_command(command)
            self.console_page.append_line(f">> {command.strip()}")

    def _handle_raw_line(self, line: str) -> None:
        """
        Inspects incoming raw lines, ensures console visibility, and parses 
        incoming text into telemetry events for the dashboard and alert log.
        """
        self.console_page.append_line(line)
        
        cleaned = line.strip()
        if not cleaned:
            return

        # Determine severity based on common log keywords
        upper_line = cleaned.upper()
        if any(w in upper_line for w in ["CRITICAL", "FAIL", "ERROR", "TAMPER", "VIOLATION"]):
            severity = Severity.CRITICAL
        elif any(w in upper_line for w in ["WARN", "ATTENTION", "CAUTION"]):
            severity = Severity.WARNING
        else:
            severity = Severity.INFO

        # Automatically wrap raw lines as AlertEvents so the UI updates immediately
        event = AlertEvent(
            received_at=datetime.now(),
            severity=severity,
            event_code="LOG" if " " in cleaned else cleaned,
            description=cleaned,
            raw_line=line,
            level_raw=cleaned
        )
        
        # Feed into model and dashboard if not already handled by strict parser signals
        self._log_model.add_event(event)
        self.dashboard_page.on_alert(event)

    def _on_connected(self) -> None:
        self.sidebar.set_connection_state("connected")
        self.dashboard_page.reset_session_stats()
        self.dashboard_page.on_connected()

    def _on_disconnected(self, reason: str) -> None:
        self.sidebar.set_connection_state("disconnected")
        self.settings_page.set_connected_ui_state(False)
        self.dashboard_page.on_disconnected(reason)

    def _on_link_error(self, message: str) -> None:
        self.sidebar.set_connection_state("error")
        self.console_page.append_line(f"[ERROR] {message}")

    def _on_status(self, status: DeviceStatus) -> None:
        self.dashboard_page.on_status(status)

    def _on_alert(self, event: AlertEvent) -> None:
        self._log_model.add_event(event)
        self.dashboard_page.on_alert(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_link()
        super().closeEvent(event)