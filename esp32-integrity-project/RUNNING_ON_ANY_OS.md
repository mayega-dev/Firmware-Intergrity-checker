# Running the Firmware Integrity Monitor System on Any OS

**Why this file is separate from the dashboard package:** it covers *both*
halves of the system together (the firmware/backend container and the
dashboard container) plus the physical USB wiring that connects them to a
real ESP32 board. That's cross-cutting information that doesn't belong
packaged inside just one half - keep this file wherever you keep your
notes, not inside `dashboard.zip`.

This assumes you have both project folders on disk:
```
firmware/      <- ESP-IDF project (the "backend")
dashboard/     <- this PySide6 app
docker-compose.yml   <- if you're using the unified project layout
```
If you only have `dashboard/` on its own, the dashboard-only sections below
still apply; skip the firmware sections.

---

## 0. The one thing that trips everyone up first

**The ESP32's USB cable does not automatically give the dashboard a
connection to the device.** The dashboard listens on a *dedicated alert
UART* configured in the firmware (`idf.py menuconfig` \u2192 "Firmware
Integrity Checker") - separate from the board's USB programming/console
port, unless you specifically reconfigured the firmware to share that port
(the "single-cable" setup below). If you skip straight to plugging in a
board and running the dashboard without reading this section, "no serial
ports found" or "board doesn't show up" is the near-certain result - not a
bug, just a wiring/configuration step that got skipped.

You have two options:

**Option A - Single cable (simplest, recommended for a first run):**
Reconfigure the firmware so the alert protocol shares the same UART as the
board's USB connection, and disable the console log on that UART so the
two data streams don't collide. One USB cable, no extra hardware. Trade-off:
no live `idf.py monitor` debug log while running this way.
```
idf.py menuconfig
  -> Component config -> ESP System Settings -> Channel for console output
     -> "No console output"
  -> Firmware Integrity Checker (top-level menu)
     -> ALERT_UART_PORT_NUM = 0
     -> ALERT_UART_TX_GPIO = 1   (U0TXD - already wired to your board's USB chip)
     -> ALERT_UART_RX_GPIO = 3   (U0RXD - already wired to your board's USB chip)
```

**Option B - Two cables (keep debug logs):** Leave the console on UART0 as
normal, and wire a second, separate USB-to-TTL adapter to whatever alert
UART pins you configure (defaults: GPIO17 TX, GPIO18 RX) - TX\u2192RX,
RX\u2192TX, GND\u2192GND between the adapter and the board. Two USB cables
into your machine, but you keep live ESP_LOG output on the first one.

Either way, once configured, rebuild and reflash before continuing.

---

## 1. Prerequisites (all OSes)

- Docker installed. Docker Desktop on Windows/macOS; `docker.io` +
  `docker-compose-v2` on Linux.
- On Linux, add yourself to the `docker` group so you don't need `sudo`
  for every command: `sudo usermod -aG docker $USER` (log out/in after).

---

## 2. Linux (native - the easiest path)

USB device passthrough and GUI forwarding both work natively here, no
extra layers.

**Firmware (build + flash):**
```
cd firmware
docker compose run --rm firmware-build-slim
ls /dev/ttyUSB* /dev/ttyACM*        # confirm your board's device path
docker compose run --rm firmware-flash-slim
```

**Dashboard:**
```
cd dashboard
sudo apt install x11-xserver-utils   # provides xhost, if you don't have it
xhost +local:docker
docker compose up --build dashboard          # Simulation Mode, no hardware needed
# --- or, with a real board plugged in: ---
PORT=/dev/ttyUSB0 docker compose run --rm dashboard-hw
```
(swap `/dev/ttyUSB0` for whatever the `ls` command above actually showed)

---

## 3. Windows (via WSL2)

Docker Desktop on Windows runs containers through WSL2. Two separate
things need setting up: getting the USB device into WSL2 at all, and
getting the dashboard's window to actually display.

### 3.1 Attach the USB device
USB devices aren't visible to WSL2 by default - `usbipd-win` bridges this:
```powershell
# Windows PowerShell, as Administrator:
winget install --interactive --exact dorssel.usbipd-win
usbipd list                      # find the BUSID for your ESP32 board
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```
Then, inside your WSL2 terminal:
```bash
ls /dev/ttyUSB0   # or /dev/ttyACM0 - should now be visible
```
Re-run `usbipd attach` every time you unplug/replug the board or reboot
Windows - it doesn't stay attached permanently.

### 3.2 Firmware build + flash
From inside WSL2, exactly the same as the Linux instructions above:
```bash
cd firmware
docker compose run --rm firmware-build-slim
docker compose run --rm firmware-flash-slim
```

### 3.3 Dashboard window (X server needed)
WSL2 has no display server of its own. Install an X server on the Windows
side - [VcXsrv](https://sourceforge.net/projects/vcxsrv/) is a common free
option:
1. Launch VcXsrv (XLaunch) with **"Disable access control"** checked (fine
   for local development use).
2. In your WSL2 terminal:
   ```bash
   export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0
   ```
   (WSL2 networking means `localhost` doesn't reach the Windows host the
   way it does on native Linux - this grabs the actual host IP instead.)
3. Run the dashboard the same way as Linux:
   ```bash
   cd dashboard
   docker compose up --build dashboard              # Simulation Mode
   PORT=/dev/ttyUSB0 docker compose run --rm dashboard-hw   # real hardware
   ```

---

## 4. macOS

Stated plainly: **Docker Desktop for Mac does not support USB device
passthrough at all.** This is a Docker Desktop limitation on this
platform, not something fixable via configuration. Practical implications:

- **Firmware build** works fine through Docker (`firmware-build-slim`
  doesn't need a device).
- **Firmware flashing** to real hardware needs a native ESP-IDF install on
  macOS instead of Docker for that one step (`brew install cmake ninja`,
  then follow Espressif's standard macOS install instructions).
- **Dashboard in Simulation Mode** works through Docker with
  [XQuartz](https://www.xquartz.org/) installed for X11 forwarding
  (similar `xhost`/`DISPLAY` idea as the Linux/WSL2 sections above).
- **Dashboard against real hardware** - skip Docker for this specific
  case and just run the dashboard natively instead, which sidesteps the
  whole X11/Docker question on this OS:
  ```bash
  cd dashboard
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  python main.py
  ```

---

## 5. Quick reference: common USB bridge chip IDs

Useful for confirming your board is actually being detected at the OS
level, and for understanding what the dashboard's Settings page is
matching against when it groups "ESP32 devices detected":

| Bridge chip | VID:PID | Typical device node |
|---|---|---|
| Silicon Labs CP2102/2104 | 10C4:EA60 | `/dev/ttyUSB0` / `COMx` |
| WCH CH340 | 1A86:7523 | `/dev/ttyUSB0` / `COMx` |
| WCH CH343/CH9102 | 1A86:55D4 | `/dev/ttyUSB0` / `COMx` |
| FTDI FT232 | 0403:6001 | `/dev/ttyUSB0` / `COMx` |
| Espressif native USB (S2/S3/C3/C6/H2) | 303A:xxxx (any PID) | `/dev/ttyACM0` / `COMx` |

---

## 6. Troubleshooting checklist

1. **Board not showing up anywhere, on any OS:** try a different USB
   cable first - many cheap cables are charge-only and carry no data.
2. **Linux: `ls /dev/ttyUSB*` shows nothing:** run `dmesg | tail`
   immediately after plugging in - it'll say whether the driver bound at
   all.
3. **WSL2: device visible in `usbipd list` but not in `ls` inside WSL2:**
   re-run `usbipd attach` - it does not persist across reboots or
   replugging.
4. **Dashboard window never appears (Linux/WSL2):** you likely skipped
   `xhost +local:docker` (Linux) or the X server isn't actually running
   (Windows/VcXsrv, macOS/XQuartz).
5. **Settings page says "No serial ports found" even though the board is
   plugged in:** check which Compose *service* you started - `dashboard`
   deliberately has no device access at all (that's what makes Simulation
   Mode always work); you need `dashboard-hw` for real hardware.
6. **Dashboard connects but nothing ever arrives:** almost always Section
   0 above - the alert UART isn't actually wired/configured the way the
   dashboard expects. Re-check the firmware's menuconfig settings.
