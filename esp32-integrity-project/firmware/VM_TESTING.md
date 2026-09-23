# Testing against a real ESP32 board from Windows, Linux, or a VM

The firmware doesn't care what's on the other end of the serial cable, so
all of this is about getting the board's USB serial device visible to
whichever OS you're running `idf.py monitor` / `esptool.py` / a dashboard
script from.

## 1. Native Windows

- Install the USB-UART bridge driver for your board's chip:
  - **CP2102/CP2104** (common on many ESP32 devkits): Silicon Labs VCP driver.
  - **CH340/CH9102**: WCH driver.
  - **Native USB** (ESP32-S2/S3/C3/C6 boards with a USB-C "USB" port, not
    "UART" port): usually enumerates as a built-in Windows USB-CDC device,
    no separate driver needed on Windows 10/11.
- Board shows up as `COMx`. Use that in `idf.py -p COMx flash monitor`.

## 2. Native Linux

- Board shows up as `/dev/ttyUSB0` (CP210x/CH340) or `/dev/ttyACM0`
  (native USB-CDC/JTAG on S2/S3/C3/C6).
- Add your user to the `dialout` group (Debian/Ubuntu) or `uucp`
  (Arch/some distros) so you don't need `sudo` for every flash:
  ```
  sudo usermod -aG dialout $USER   # log out/in to take effect
  ```
- `idf.py -p /dev/ttyUSB0 flash monitor`

## 3. Testing from inside a VM

The board's USB device has to be *passed through* to the VM — a VM can't
see host serial ports unless you explicitly forward the USB device.

### VirtualBox (host: Windows or Linux, guest: Linux or Windows)
1. Install the **VirtualBox Extension Pack** (needed for USB 2.0/3.0
   passthrough).
2. Guest must be powered off or you attach live via the USB icon in the
   running-VM status bar.
3. VM Settings → **USB** → enable USB controller → add a filter matching
   your board's VID:PID (e.g. `10C4:EA60` for CP2102, `1A86:7523` for
   CH340) so it auto-attaches on plug-in.
4. Inside the guest, the board appears exactly as in native Linux/Windows
   above (`/dev/ttyUSB0` or `COMx`).

### VMware Workstation/Fusion
- Similar flow: VM → Removable Devices → select the CP210x/CH340/USB-CDC
  device → Connect (Disconnect from host).
- Fusion on macOS hosts needs the device connected to the VM, not macOS,
  before `idf.py monitor` will see it in the guest.

### WSL2 (Windows host, Linux environment) — no full VM needed
WSL2 doesn't expose USB devices by default. Use **usbipd-win**:
```powershell
# On Windows (PowerShell, admin):
winget install --interactive --exact dorssel.usbipd-win
usbipd list                      # find the BUSID for your board
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```
```bash
# Inside WSL2:
ls /dev/ttyUSB0    # or /dev/ttyACM0
idf.py -p /dev/ttyUSB0 flash monitor
```
Re-run `usbipd attach` each time you unplug/replug the board or reboot
Windows.

### Hyper-V
Hyper-V has no built-in generic USB passthrough for guests other than
"Enhanced Session" RDP redirection for a handful of device classes. The
practical options are:
- Use **usbipd-win** the same way as the WSL2 case above (it works for any
  Hyper-V/WSL2 Linux guest, not just WSL2 specifically), or
- Run `idf.py monitor` on the Windows host instead of inside the Hyper-V
  guest, and only cross-compile / run host-side test scripts in the VM.

## 4. If you only need to *simulate* the board (no hardware attached)

ESP-IDF ships **QEMU** targets for `esp32` and `esp32c3` that boot real
firmware images without hardware, which is useful for CI or for exercising
the boot-time rollback/logger logic without a board on the desk:
```
idf.py --preview set-target esp32c3
idf.py build
idf.py qemu monitor
```
This only covers what QEMU emulates (CPU, flash, basic peripherals) — it
does **not** emulate the UART-connected desktop dashboard link or real
flash tampering, so hardware-in-the-loop testing (per the proposal's
§3.5.3 security testing / tamper-simulation plan) still needs a physical
board or the `ENABLE_TAMPER_SIMULATION` build flag on real hardware.

## Quick reference: common devkit VID:PID pairs

| Bridge chip | VID:PID     | Typical device node          |
|-------------|-------------|-------------------------------|
| CP2102/2104 | 10C4:EA60   | `/dev/ttyUSB0` / `COMx`       |
| CH340/CH9102| 1A86:7523 / 1A86:55D4 | `/dev/ttyUSB0` / `COMx` |
| Native USB-CDC (S2/S3/C3/C6) | varies by board | `/dev/ttyACM0` / `COMx` |
