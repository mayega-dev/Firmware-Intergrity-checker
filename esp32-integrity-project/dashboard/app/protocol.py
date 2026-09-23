"""
Wire protocol for the ESP32 Firmware Integrity Checker's dedicated alert
UART (see firmware/main/serial_comm.c - NOT the ESP-IDF console/log UART;
this is a second, separate port configured in `idf.py menuconfig` ->
"Firmware Integrity Checker").

Two frame types are emitted by the device, both newline-terminated:

    ::STATUS:<fw_version>:<hardware_revision>::
    ::ALERT:<LEVEL>:<EVENT_CODE>::

`STATUS` is sent once at boot, right after the alert UART driver comes up.
`ALERT` is sent for every security event (see EVENT_CATALOG below for the
codes this firmware build actually emits).

Two commands can be sent *to* the device (see integrity_checker.c):

    ::POLL::      -> trigger an immediate verification sweep
    ::TAMPER::    -> DEBUG BUILDS ONLY (ENABLE_TAMPER_SIMULATION=1):
                     inject a simulated tamper event for testing

This module is intentionally dependency-free (no PySide6 import) so it can
be unit-tested or reused headlessly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


_STATUS_RE = re.compile(r"::STATUS:([^:]*):([^:]*)::")
_ALERT_RE = re.compile(r"::ALERT:([A-Za-z0-9_]*):([A-Za-z0-9_]*)::")


class Severity(str, Enum):
    """Normalized severity, independent of the device's raw level string."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_level(cls, level: str) -> "Severity":
        level = (level or "").upper()
        if level == "CRITICAL":
            return cls.CRITICAL
        if level == "WARNING":
            return cls.WARNING
        if level == "INFO":
            return cls.INFO
        return cls.UNKNOWN


# What each event code this firmware build actually emits means, in plain
# language, for display in the log/console. Unknown codes still display
# fine (protocol.py never rejects them) - this dict is presentation-only.
EVENT_CATALOG: dict[str, str] = {
    "STATUS_SAFE": "Runtime integrity check passed - firmware matches the trusted baseline.",
    "FIRMWARE_TAMPERED": "Integrity violation: running firmware no longer matches the golden hash.",
    "ROLLBACK_ATTEMPT_BLOCKED": "Boot halted: firmware version is older than the anti-rollback floor.",
}


@dataclass
class DeviceStatus:
    """Parsed result of a ::STATUS:...:: handshake frame."""

    fw_version: str
    hardware_revision: str
    received_at: datetime = field(default_factory=datetime.now)


@dataclass
class AlertEvent:
    """Parsed result of an ::ALERT:...:: frame."""

    level_raw: str
    event_code: str
    severity: Severity
    description: str
    received_at: datetime = field(default_factory=datetime.now)
    raw_line: str = ""


def parse_line(line: str) -> DeviceStatus | AlertEvent | None:
    """
    Parse one line of device output. Returns a DeviceStatus, an AlertEvent,
    or None if the line doesn't match either known frame (e.g. it's stray
    console/log noise that leaked onto the wrong UART, or a partial read).
    """
    line = line.strip()
    if not line:
        return None

    m = _STATUS_RE.search(line)
    if m:
        fw_version, hw_revision = m.group(1), m.group(2)
        return DeviceStatus(fw_version=fw_version or "unknown", hardware_revision=hw_revision or "unknown")

    m = _ALERT_RE.search(line)
    if m:
        level_raw, event_code = m.group(1), m.group(2)
        severity = Severity.from_level(level_raw)
        description = EVENT_CATALOG.get(event_code, f"Unrecognized event code '{event_code}'.")
        return AlertEvent(
            level_raw=level_raw or "UNKNOWN",
            event_code=event_code or "UNKNOWN",
            severity=severity,
            description=description,
            raw_line=line,
        )

    return None


# Outgoing commands (see integrity_checker.c's command parser).
CMD_POLL = "::POLL::\n"
CMD_TAMPER = "::TAMPER::\n"  # only has an effect on ENABLE_TAMPER_SIMULATION=1 builds
