from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.device_link import available_ports

COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
PORT_REFRESH_INTERVAL_MS = 2000


class SettingsPage(QWidget):
    """
    Professional-grade settings page styled with an advanced dark engineering
    aesthetic, featuring clear card framing, distinct typography, and structured controls.
    """
    connect_requested = Signal(str, int)  # port, baud  (port == "__SIMULATE__" for simulation mode) 
    disconnect_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Header Card ──────────────────────────────────────────────────────
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

        title = QLabel("Hardware & Connection Settings")
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 20px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel(
            "Connect to the device's dedicated alert UART - a separate port from the "
            "board's console/programming port, configured in idf.py menuconfig → "
            "\"Firmware Integrity Checker\"."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            color: #94A3B8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            line-height: 1.6;
            background: transparent;
            border: none;
        """)
        header_lay.addWidget(title)
        header_lay.addWidget(subtitle)
        root.addWidget(header_card)

        # ── Configuration Form Card ──────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            QFrame#card {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        form_wrap = QVBoxLayout(card)
        form_wrap.setContentsMargins(24, 24, 24, 24)
        form_wrap.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        form_label_style = """
            color: #F8FAFC;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """

        input_widget_style = """
            QComboBox {
                background: #070A10;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #38BDF8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #0B0F19;
                color: #F8FAFC;
                selection-background-color: #1E293B;
                selection-color: #38BDF8;
                border: 1px solid #334155;
                outline: none;
                padding: 4px;
            }
        """

        # Serial Port Row
        port_row = QHBoxLayout()
        port_row.setSpacing(10)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(280)
        self.port_combo.setStyleSheet(input_widget_style)
        self.port_combo.currentIndexChanged.connect(self._on_port_selection_changed)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #334155;
                border-color: #38BDF8;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(refresh_btn)
        
        port_label = QLabel("Serial Port")
        port_label.setStyleSheet(form_label_style)
        form.addRow(port_label, port_row)

        # Port Summary Label
        self.port_summary_label = QLabel("")
        self.port_summary_label.setObjectName("cardTitle")
        self.port_summary_label.setWordWrap(True)
        self.port_summary_label.setStyleSheet("""
            color: #94A3B8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        form.addRow("", self.port_summary_label)

        # Baud Rate Row
        self.baud_combo = QComboBox()
        self.baud_combo.addItems([str(b) for b in COMMON_BAUD_RATES]) 
        self.baud_combo.setCurrentText("115200") 
        self.baud_combo.setStyleSheet(input_widget_style)
        
        baud_label = QLabel("Baud Rate")
        baud_label.setStyleSheet(form_label_style)
        form.addRow(baud_label, self.baud_combo)

        # Simulation Mode Row
        self.simulate_check = QCheckBox("Simulation mode (no hardware needed)")
        self.simulate_check.setCursor(Qt.PointingHandCursor)
        self.simulate_check.setToolTip(
            "Generates synthetic STATUS/ALERT traffic locally so you can demo or "
            "develop the dashboard without a board attached."
        ) 
        self.simulate_check.setStyleSheet("""
            QCheckBox {
                color: #F8FAFC;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #334155;
                border-radius: 4px;
                background: #070A10;
            }
            QCheckBox::indicator:checked {
                background: #38BDF8;
                border-color: #38BDF8;
            }
            QCheckBox::indicator:disabled {
                background: #1E293B;
                border-color: #1E293B;
            }
        """)
        self.simulate_check.toggled.connect(self._on_simulate_toggled)
        form.addRow("", self.simulate_check)

        form_wrap.addLayout(form)

        # ── Action Buttons Row ───────────────────────────────────────────────
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        
        self.connect_btn = QPushButton("Connect Device")
        self.connect_btn.setObjectName("primaryButton")
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #0284C7;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #38BDF8;
                color: #070A10;
            }
            QPushButton:disabled {
                background: #1E293B;
                color: #64748B;
            }
        """)
        self.connect_btn.clicked.connect(self._on_connect_clicked)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False) 
        self.disconnect_btn.setCursor(Qt.PointingHandCursor)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #F87171;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px 24px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #7F1D1D;
                border-color: #F87171;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background: #0B0F19;
                color: #334155;
                border-color: #1E293B;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)

        button_row.addWidget(self.connect_btn)
        button_row.addWidget(self.disconnect_btn)
        button_row.addStretch(1)
        form_wrap.addLayout(button_row)

        root.addWidget(card)
        root.addStretch(1)

        self.refresh_ports()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(PORT_REFRESH_INTERVAL_MS) 
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start()

    def refresh_ports(self) -> None:
        previous_device = self.port_combo.currentData() 
        self.port_combo.blockSignals(True)
        self.port_combo.clear() 

        ports = available_ports() 
        esp_ports = [p for p in ports if p.is_likely_esp32] 
        other_ports = [p for p in ports if not p.is_likely_esp32] 

        if not ports:
            self.port_combo.addItem("No serial ports found", None) 
            self.port_combo.setEnabled(False) 
            self.port_summary_label.setText("Plug in a board and click Refresh, or wait a couple seconds.") 
        else:
            self.port_combo.setEnabled(not self.simulate_check.isChecked()) 

            if esp_ports:
                self.port_combo.addItem("── ESP32 devices detected ──", None) 
                for p in esp_ports:
                    self.port_combo.addItem(f"{p.device}  —  {p.match_reason}", p.device) 

            if other_ports:
                if esp_ports:
                    self.port_combo.insertSeparator(self.port_combo.count()) 
                self.port_combo.addItem("── Other serial ports ──", None) 
                for p in other_ports:
                    self.port_combo.addItem(f"{p.device}  —  {p.description}", p.device) 

            restored = False
            if previous_device:
                idx = self.port_combo.findData(previous_device) 
                if idx >= 0:
                    self.port_combo.setCurrentIndex(idx) 
                    restored = True
            if not restored and esp_ports:
                idx = self.port_combo.findData(esp_ports[0].device) 
                if idx >= 0:
                    self.port_combo.setCurrentIndex(idx) 

            if esp_ports and other_ports:
                self.port_summary_label.setText(
                    f"{len(esp_ports)} likely ESP32 device(s), {len(other_ports)} other serial port(s)."
                ) 
            elif esp_ports:
                self.port_summary_label.setText(f"{len(esp_ports)} likely ESP32 device(s) detected.") 
            else:
                self.port_summary_label.setText(
                    f"No recognized ESP32 USB bridge found among {len(other_ports)} serial port(s) - "
                    "check the board is plugged in, or pick manually below."
                ) 

        self.port_combo.blockSignals(False)
        self._update_mutual_exclusivity()

    def _auto_refresh(self) -> None:
        if not self.connect_btn.isEnabled():
            return  
        self.refresh_ports() 

    def _on_port_selection_changed(self) -> None:
        self._update_mutual_exclusivity()

    def _update_mutual_exclusivity(self) -> None:
        """Enforces that physical hardware selection and simulation mode are mutually exclusive."""
        has_valid_port = self.port_combo.currentData() is not None and self.port_combo.isEnabled()
        
        if has_valid_port:
            # If a real device port is selected, force simulation mode off and disable the checkbox
            if self.simulate_check.isChecked():
                self.simulate_check.blockSignals(True)
                self.simulate_check.setChecked(False)
                self.simulate_check.blockSignals(False)
            self.simulate_check.setEnabled(False)
        else:
            # If no physical port is selected, allow user to toggle simulation mode
            self.simulate_check.setEnabled(True)

    def _on_simulate_toggled(self, checked: bool) -> None:
        if checked:
            # When simulation mode is enabled, clear/disable hardware port and baud selection
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
        else:
            self.port_combo.setEnabled(self.port_combo.count() > 0)
            self.baud_combo.setEnabled(True)
        self._update_mutual_exclusivity()

    def _on_connect_clicked(self) -> None:
        if self.simulate_check.isChecked():
            self.connect_requested.emit("__SIMULATE__", 0) 
            return
        port = self.port_combo.currentData() 
        if not port:
            return  
        baud = int(self.baud_combo.currentText()) 
        self.connect_requested.emit(port, baud) 

    def set_connected_ui_state(self, connected: bool) -> None:
        self.connect_btn.setEnabled(not connected) 
        self.disconnect_btn.setEnabled(connected) 
        
        if connected:
            self.port_combo.setEnabled(False) 
            self.baud_combo.setEnabled(False) 
            self.simulate_check.setEnabled(False)
        else:
            is_simulating = self.simulate_check.isChecked()
            self.port_combo.setEnabled(not is_simulating and self.port_combo.count() > 0) 
            self.baud_combo.setEnabled(not is_simulating) 
            self._update_mutual_exclusivity()