"""
Unit tests for app.protocol - the only module in this app with zero PySide6
dependency, so it's the one piece that can be tested with plain `pytest` on
any machine, no Qt install required.

Run with:  pytest test_protocol.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.protocol import AlertEvent, DeviceStatus, Severity, parse_line  # noqa: E402


def test_parses_status_frame():
    result = parse_line("::STATUS:1.0.0:ESP32-S3::")
    assert isinstance(result, DeviceStatus)
    assert result.fw_version == "1.0.0"
    assert result.hardware_revision == "ESP32-S3"


def test_parses_critical_alert():
    result = parse_line("::ALERT:CRITICAL:FIRMWARE_TAMPERED::")
    assert isinstance(result, AlertEvent)
    assert result.severity == Severity.CRITICAL
    assert result.event_code == "FIRMWARE_TAMPERED"
    assert "hash" in result.description.lower()


def test_parses_info_alert():
    result = parse_line("::ALERT:INFO:STATUS_SAFE::")
    assert isinstance(result, AlertEvent)
    assert result.severity == Severity.INFO


def test_unrecognized_event_code_still_parses():
    result = parse_line("::ALERT:WARNING:SOME_NEW_CODE_FROM_A_FUTURE_FIRMWARE::")
    assert isinstance(result, AlertEvent)
    assert result.severity == Severity.WARNING
    assert "unrecognized" in result.description.lower()


def test_unknown_severity_level_maps_to_unknown():
    result = parse_line("::ALERT:WEIRD_LEVEL:SOME_CODE::")
    assert isinstance(result, AlertEvent)
    assert result.severity == Severity.UNKNOWN


def test_garbage_line_returns_none():
    assert parse_line("this is not a protocol frame") is None
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_trailing_whitespace_and_newline_tolerated():
    result = parse_line("::ALERT:CRITICAL:FIRMWARE_TAMPERED::\r\n")
    assert isinstance(result, AlertEvent)
    assert result.event_code == "FIRMWARE_TAMPERED"


def test_console_log_noise_on_the_wire_is_ignored():
    # If the alert UART ever picks up stray ESP_LOG output (e.g. a
    # misconfigured board where console and alert UART collide), it must
    # not be misparsed as a protocol frame.
    assert parse_line("I (312) MAIN: Starting Firmware Security Engine v1.0.0...") is None


if __name__ == "__main__":
    # Allow running without pytest installed too.
    import inspect

    failures = 0
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
