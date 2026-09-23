from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.models import AlertLogModel

_CONTAINER_EXPORTS_DIR = Path("/data/exports") 


class LogPage(QWidget):
    """
    Professional-grade alert log view featuring a clear header card, modern table styling,
    integrated search/filtering toolbar, and robust CSV export options .
    """

    def __init__(self, log_model: AlertLogModel, parent=None):
        super().__init__(parent)
        self._log_model = log_model

        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(log_model)
        self._proxy.setFilterKeyColumn(-1)  # search across all columns 
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

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

        title = QLabel("Device Alert Log & Audit Trail")
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 20px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel("Complete immutable session history of every event received from the hardware device.")
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

        # ── Main Content Card (Toolbar + Table) ──────────────────────────────
        content_card = QFrame()
        content_card.setStyleSheet("""
            QFrame {
                background: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)
        cc_layout = QVBoxLayout(content_card)
        cc_layout.setContentsMargins(20, 20, 20, 20)
        cc_layout.setSpacing(16)

        # Toolbar Row
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by event, description, severity…")
        self.search_box.textChanged.connect(self._proxy.setFilterFixedString)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #070A10;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #38BDF8;
                background: #0B0F19;
            }
        """)

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

        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All severities", "CRITICAL", "WARNING", "INFO", "UNKNOWN"]) 
        self.severity_filter.currentTextChanged.connect(self._apply_severity_filter)
        self.severity_filter.setStyleSheet(input_widget_style)

        export_btn = QPushButton("Export CSV")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
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
        export_btn.clicked.connect(self._export_csv)

        clear_btn = QPushButton("Clear Log")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #450A0A;
                color: #F87171;
                border: 1px solid #7F1D1D;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #7F1D1D;
                border-color: #F87171;
                color: #FFFFFF;
            }
        """)
        clear_btn.clicked.connect(self._clear_log)

        toolbar.addWidget(self.search_box, 1)
        toolbar.addWidget(self.severity_filter)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(clear_btn)
        cc_layout.addLayout(toolbar)

        # Table View
        self.table = QTableView()
        self.table.setModel(self._proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet("""
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
        cc_layout.addWidget(self.table, 1)

        root.addWidget(content_card, 1)

    def _apply_severity_filter(self, text: str) -> None:
        if text == "All severities":
            self._proxy.setFilterRegularExpression("")
            self._proxy.setFilterKeyColumn(-1)
        else:
            self._proxy.setFilterKeyColumn(1)  # Severity column 
            self._proxy.setFilterFixedString(text)

    def _clear_log(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Log",
            "Clear all logged events for this session? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._log_model.clear()

    def _export_csv(self) -> None:
        events = self._log_model.events()
        if not events:
            QMessageBox.information(self, "Export CSV", "No events to export yet.")
            return

        default_name = f"alert_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_dir = _CONTAINER_EXPORTS_DIR if _CONTAINER_EXPORTS_DIR.is_dir() else Path.home() 
        default_path = str(default_dir / default_name)

        path, _ = QFileDialog.getSaveFileName(self, "Export Alert Log", default_path, "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "severity", "event_code", "description", "raw_line"])
            for e in events:
                writer.writerow(
                    [e.received_at.isoformat(timespec="seconds"), e.severity.value, e.event_code, e.description, e.raw_line]
                )

        note = ""
        if _CONTAINER_EXPORTS_DIR.is_dir() and str(Path(path).parent) == str(_CONTAINER_EXPORTS_DIR):
            note = "\n\nThis is inside the container's mounted exports/ folder, so it's also on your host machine at esp32-integrity-project/exports/." 
        QMessageBox.information(self, "Export CSV", f"Exported {len(events)} events to:\n{path}{note}")