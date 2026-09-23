# Porting notes: ESP32-S3-only → any ESP32 target

## Why the code barely had to change

Most of this project was already chip-agnostic, because it's built entirely
on ESP-IDF's hardware-abstraction APIs rather than talking to registers
directly:

| Subsystem              | API used                              | Portable as-is? |
|-------------------------|----------------------------------------|------------------|
| Firmware hashing         | `esp_partition_read()` + `mbedtls_sha256_*` | Yes |
| Anti-rollback counter    | `nvs_get_i32/nvs_set_i32`             | Yes |
| Secure event log          | `nvs_get_blob/nvs_set_blob`            | Yes |
| Reference hash storage    | `nvs_get_blob/nvs_set_blob`            | Yes |
| Task scheduling           | FreeRTOS (`xTaskCreate`, `vTaskDelay`) | Yes |

The only genuinely chip-specific things were two hardcoded assumptions:
a literal `"ESP32-S3-N8R8"` version string, and a hardcoded UART port/pin
pair for the dashboard alert channel. Both are fixed now.

## What changed

1. **`firmware_config.h` — `HARDWARE_REVISION`**
   Was a fixed string. Now derived at compile time from the
   `CONFIG_IDF_TARGET_*` macro ESP-IDF sets automatically based on
   `idf.py set-target <chip>`, so the same source tree self-labels
   correctly for ESP32, S2, S3, C2, C3, C6, H2.

2. **`Kconfig.projbuild` (new) + `serial_comm.h/.c`**
   The alert UART port/TX/RX pins were `#define`d to `UART_NUM_1` / GPIO
   17 / GPIO 18, which happen to be valid on ESP32/S2/S3 devkits but are
   not guaranteed to be free (or even exist) on every board — e.g.
   GPIO17/18 are used for PSRAM on `-WROVER` modules, and pin-count is
   much lower on the C-series chips. These are now `idf.py menuconfig`
   settings under **"Firmware Integrity Checker"**, so you pick pins that
   are actually free on *your* board.

3. **Console-collision guard**
   `serial_comm_init()` now checks the active console configuration
   (`CONFIG_ESP_CONSOLE_UART` / `CONFIG_ESP_CONSOLE_UART_NUM`) at compile
   time and refuses to double-book the same UART for both `ESP_LOG` output
   and the alert protocol. This matters more once other chips are in
   scope, because on native-USB parts (S2/S3/C3/C6) the console is often
   routed to USB-CDC or USB-Serial-JTAG instead of UART0 — so "just use
   UART1 to avoid UART0" isn't a safe universal rule anymore.

4. **`integrity_checker.c`**
   Removed a second, independent `#define UART_PORT UART_NUM_1` that
   duplicated (and could silently drift out of sync with) the one in
   `serial_comm.c`. It now includes `serial_comm.h` and reuses
   `ALERT_UART_PORT`, and skips the UART read entirely if
   `serial_comm_is_ready()` is false instead of reading from a
   never-initialized port.

## What did *not* need to change, and why

- **SHA-256 hardware acceleration** (`USE_HARDWARE_SHA256_ACCEL` in
  `firmware_config.h`) is a documentation flag only — the actual on/off
  switch is the ESP-IDF Kconfig option `CONFIG_MBEDTLS_HARDWARE_SHA`.
  mbedTLS auto-selects the right hardware SHA engine (or falls back to
  software) per target; `crypto.c` never needed to know which.
- **`CMakeLists.txt` (both root and `main/`)** have no chip-specific
  settings — target selection lives entirely in `sdkconfig`
  (`idf.py set-target esp32c3`, etc.), not in the build scripts.

## Per-target checklist before flashing a new board

1. `idf.py set-target <esp32|esp32s2|esp32s3|esp32c2|esp32c3|esp32c6|esp32h2>`
2. `idf.py menuconfig` → **Firmware Integrity Checker** → set
   `ALERT_UART_PORT_NUM` / `ALERT_UART_TX_GPIO` / `ALERT_UART_RX_GPIO` to
   pins that are free on the specific module you're using (check the
   board's pinout diagram — flash/PSRAM-strapped pins vary by module).
3. Confirm `MONITORED_PARTITION_LABEL` ("factory" by default) matches an
   actual entry in that target's partition table.
4. If you rely on `USE_HARDWARE_SHA256_ACCEL`, confirm
   `CONFIG_MBEDTLS_HARDWARE_SHA=y` is actually set for that target in
   `menuconfig` (Component config → mbedTLS).
5. Rebuild: `idf.py build`.

## Host side (Windows / Linux, physical board or VM)

Nothing in this firmware cares what OS is reading its serial output — that
was already true. `idf.py monitor` / `esptool.py` / any terminal or
`pyserial` script works identically on Windows and Linux; the only
OS-specific piece is which *driver* shows up as a COM port vs. `/dev/tty*`
(see `VM_TESTING.md` for driver names and VM passthrough steps).
