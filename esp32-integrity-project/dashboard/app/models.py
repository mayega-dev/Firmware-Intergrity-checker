from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from app.protocol import AlertEvent, Severity

SEVERITY_COLORS = {
    Severity.CRITICAL: QColor("#ef4444"),
    Severity.WARNING: QColor("#fbbf24"),
    Severity.INFO: QColor("#34d399"),
    Severity.UNKNOWN: QColor("#8b95a5"),
}

_COLUMNS = ["Time", "Severity", "Event", "Description"]


class AlertLogModel(QAbstractTableModel):
    """Append-only log of every AlertEvent received this session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._events: list[AlertEvent] = []

    def add_event(self, event: AlertEvent) -> None:
        row = len(self._events)
        self.beginInsertRows(QModelIndex(), row, row)
        self._events.append(event)
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._events.clear()
        self.endResetModel()

    def events(self) -> list[AlertEvent]:
        return list(self._events)

    def counts_by_severity(self) -> dict[Severity, int]:
        out = {s: 0 for s in Severity}
        for e in self._events:
            out[e.severity] += 1
        return out

    # --- Qt model interface -------------------------------------------------
    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt naming
        return 0 if parent.isValid() else len(self._events)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return _COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        event = self._events[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return event.received_at.strftime("%H:%M:%S")
            if col == 1:
                return event.severity.value
            if col == 2:
                return event.event_code
            if col == 3:
                return event.description

        if role == Qt.ForegroundRole and col == 1:
            return SEVERITY_COLORS.get(event.severity, SEVERITY_COLORS[Severity.UNKNOWN])

        if role == Qt.ToolTipRole:
            return event.raw_line

        return None
