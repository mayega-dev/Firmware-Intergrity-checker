"""
QThread-based link to the device's alert UART. Owns the serial port
exclusively (one thread does all reads AND writes, via a command queue)
to avoid the read/write thread-safety ambiguity pyserial doesn't guarantee.

Two concrete links share the same signal interface so the rest of the app
(main_window.py) doesn't care which one is active:

    SerialLink      - real hardware over a COM port / /dev/tty*
    SimulatorLink   - synthetic traffic, for demoing/screenshotting the UI
                      or developing the dashboard without a board attached
"""
from __future__ import annotations

import queue
import random
import time
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from app.protocol import AlertEvent, DeviceStatus, parse_line

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - surfaced to the UI instead of crashing at import time
    serial = None
    list_ports = None


# USB VID:PID pairs for the USB-UART bridge chips found on essentially every
# ESP32 devkit, plus Espressif's own VID for native-USB boards (S2/S3/C3/C6/H2
# in USB-CDC or USB-Serial-JTAG mode - PID varies by mode/IDF version, so any
# PID under this VID is treated as a match rather than enumerating each one).
_KNOWN_BRIDGE_CHIPS: dict[tuple[int, int], str] = {
    (0x10C4, 0xEA60): "Silicon Labs CP2102/CP2104 USB-UART bridge",
    (0x1A86, 0x7523): "WCH CH340 USB-UART bridge",
    (0x1A86, 0x55D4): "WCH CH9102/CH343 USB-UART bridge",
    (0x0403, 0x6001): "FTDI FT232 USB-UART bridge",
    (0x0403, 0x6010): "FTDI FT2232 USB-UART bridge",
    (0x0403, 0x6014): "FTDI FT232H USB-UART bridge",
}
_ESPRESSIF_VID = 0x303A  # native USB (USB-Serial-JTAG / USB-CDC) - any PID


def _classify(vid: int | None, pid: int | None) -> tuple[bool, str]:
    """Returns (is_likely_esp32, human-readable reason)."""
    if vid == _ESPRESSIF_VID:
        return True, "Espressif native USB (USB-Serial-JTAG/CDC)"
    if vid is not None and pid is not None and (vid, pid) in _KNOWN_BRIDGE_CHIPS:
        return True, _KNOWN_BRIDGE_CHIPS[(vid, pid)]
    return False, ""


@dataclass
class PortInfo:
    device: str  # e.g. "COM3" or "/dev/ttyUSB0"
    description: str
    vid: int | None
    pid: int | None
    is_likely_esp32: bool
    match_reason: str  # only meaningful when is_likely_esp32 is True


def available_ports() -> list[PortInfo]:
    """
    Every serial port currently visible to the OS, classified as a likely
    ESP32 (recognized USB-UART bridge chip or Espressif's own native-USB
    VID) or not. This is what lets the Settings page separate "your ESP32
    board" from things like a Bluetooth virtual COM port or an internal
    modem, which the OS lists right alongside real USB devices with no
    indication either way otherwise.

    Sorted with likely-ESP32 ports first, each group alphabetical.
    """
    if list_ports is None:
        return []

    infos = []
    for p in list_ports.comports():
        is_esp32, reason = _classify(p.vid, p.pid)
        infos.append(
            PortInfo(
                device=p.device,
                description=p.description or "Unknown device",
                vid=p.vid,
                pid=p.pid,
                is_likely_esp32=is_esp32,
                match_reason=reason,
            )
        )
    infos.sort(key=lambda i: (not i.is_likely_esp32, i.device))
    return infos


class DeviceLink(QThread):
    """Common signal contract for both SerialLink and SimulatorLink."""

    connected = Signal()
    disconnected = Signal(str)  # reason
    status_received = Signal(object)  # DeviceStatus
    alert_received = Signal(object)  # AlertEvent
    raw_line_received = Signal(str)  # every line, for the console view
    link_error = Signal(str)

    def send_command(self, command: str) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    def stop(self) -> None:
        self._running = False


class SerialLink(DeviceLink):
    """Real hardware link over pyserial."""

    def __init__(self, port: str, baud_rate: int = 115200, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud_rate = baud_rate
        self._running = True
        self._out_queue: "queue.Queue[str]" = queue.Queue()

    def send_command(self, command: str) -> None:
        self._out_queue.put_nowait(command)

    def run(self) -> None:  # noqa: C901 - straightforward top-to-bottom loop, not actually complex
        if serial is None:
            self.link_error.emit(
                "pyserial is not installed. Run: pip install -r requirements.txt"
            )
            return

        try:
            ser = serial.Serial(self.port, self.baud_rate, timeout=0.2)
        except serial.SerialException as exc:
            self.link_error.emit(f"Could not open {self.port}: {exc}")
            return

        self.connected.emit()
        try:
            while self._running:
                # Drain any queued outgoing commands first.
                while not self._out_queue.empty():
                    try:
                        cmd = self._out_queue.get_nowait()
                        ser.write(cmd.encode("ascii", errors="replace"))
                    except queue.Empty:
                        break
                    except serial.SerialException as exc:
                        self.link_error.emit(f"Write failed: {exc}")

                try:
                    raw = ser.readline()
                except serial.SerialException as exc:
                    self.link_error.emit(f"Lost connection to {self.port}: {exc}")
                    break

                if not raw:
                    continue  # readline() timeout, nothing arrived - loop again

                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                self.raw_line_received.emit(line)

                parsed = parse_line(line)
                if isinstance(parsed, DeviceStatus):
                    self.status_received.emit(parsed)
                elif isinstance(parsed, AlertEvent):
                    self.alert_received.emit(parsed)
                # else: non-protocol noise on the wire - already surfaced via
                # raw_line_received for the console view, nothing else to do.
        finally:
            try:
                ser.close()
            except Exception:
                pass
            self.disconnected.emit("Link closed")


class SimulatorLink(DeviceLink):
    """
    Synthetic device traffic for demoing/screenshotting the dashboard, or
    developing the UI without a board on the desk. Mirrors real device
    timing/behavior reasonably closely: a STATUS handshake once at
    "boot", periodic STATUS_SAFE heartbeats, and occasional injected
    incidents.
    """

    _EVENT_WEIGHTS: list[tuple[str, str, float]] = [
        ("INFO", "STATUS_SAFE", 0.90),
        ("CRITICAL", "FIRMWARE_TAMPERED", 0.06),
        ("CRITICAL", "ROLLBACK_ATTEMPT_BLOCKED", 0.04),
    ]

    def __init__(self, heartbeat_seconds: float = 3.0, parent=None):
        super().__init__(parent)
        self.heartbeat_seconds = heartbeat_seconds
        self._running = True

    def send_command(self, command: str) -> None:
        # Simulated device "handles" ::POLL:: by immediately emitting a
        # fresh status-safe alert, same as the real integrity_checker.c
        # would after a manual poll.
        if command.strip() == "::POLL::":
            self._emit_alert("INFO", "STATUS_SAFE")
        elif command.strip() == "::TAMPER::":
            self._emit_alert("CRITICAL", "FIRMWARE_TAMPERED")

    def _emit_alert(self, level: str, code: str) -> None:
        line = f"::ALERT:{level}:{code}::"
        self.raw_line_received.emit(line)
        parsed = parse_line(line)
        if isinstance(parsed, AlertEvent):
            self.alert_received.emit(parsed)

    def run(self) -> None:
        self.connected.emit()

        boot_line = "::STATUS:1.0.0-sim:ESP32-S3 (Simulated)::"
        self.raw_line_received.emit(boot_line)
        parsed = parse_line(boot_line)
        if isinstance(parsed, DeviceStatus):
            self.status_received.emit(parsed)

        elapsed = 0.0
        while self._running:
            time.sleep(0.2)
            elapsed += 0.2
            if elapsed >= self.heartbeat_seconds:
                elapsed = 0.0
                codes = self._EVENT_WEIGHTS
                level, code, _ = random.choices(codes, weights=[w for *_, w in codes], k=1)[0]
                self._emit_alert(level, code)

        self.disconnected.emit("Simulation stopped")
