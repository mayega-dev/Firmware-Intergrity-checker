# Running the dashboard via Docker

## Prerequisites (Linux)

```
sudo apt install docker.io docker-compose-v2 x11-xserver-utils
sudo usermod -aG docker $USER   # log out/in afterward
```

## Quickest path: Simulation Mode, no hardware

```
export DISPLAY
xhost +local:docker
docker compose up --build
```
The dashboard window should appear on your desktop like any other app.
Go to Settings → check **Simulation mode** → Connect. This is the fastest
way to confirm the whole X11/Docker/PySide6 chain actually works before
worrying about serial hardware at all.

**`xhost +local:docker`** is the one genuinely necessary extra step for
running a GUI app in Docker - by default your X server refuses connections
from anything outside your normal session, including containers. This
command authorizes local Docker containers to open windows on your
display. It resets when you log out, so you'll run it again next session
(or add it to your shell profile if you use this often).

*More locked-down alternative:* instead of `xhost +local:docker` (which
authorizes every local container), mount your existing X auth cookie
instead:
```
docker run --rm -it \
    -e DISPLAY="$DISPLAY" -e XAUTHORITY=/tmp/.Xauthority \
    -v "$HOME/.Xauthority":/tmp/.Xauthority:ro \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    firmware-integrity-dashboard:latest
```

## With a real board attached

```
./scripts/run-with-device.sh              # defaults to /dev/ttyUSB0
./scripts/run-with-device.sh /dev/ttyACM0
```
This builds the image if needed, handles the `xhost` step, and adds
`--device` for serial passthrough on top of the X11 forwarding - both at
once, since you need both for a real hardware run.

## Windows (WSL2)

Two separate things have to work together here:
1. **The window itself**: install an X server on Windows (VcXsrv is the
   common free option), run it with "Disable access control" checked for
   local testing, then from inside WSL2: `export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0`
   (WSL2's networking means `localhost` doesn't reach the Windows host the
   way it does on native Linux - this grabs the actual host IP instead).
2. **The board**: attach it via usbipd exactly as in
   `../firmware/VM_TESTING.md`'s WSL2 section, then run
   `./scripts/run-with-device.sh` from the WSL2 shell.

## macOS

Docker Desktop for Mac has no USB device passthrough (a Docker Desktop
limitation). Two honest options:
- Run the dashboard in Docker with **Simulation Mode only** (install
  XQuartz for the X11 forwarding piece, similar idea to the WSL2 case
  above) - fine for demoing the UI, not for real hardware.
- For real hardware on a Mac, skip Docker for the dashboard and just run
  it natively: `python3 -m venv venv && source venv/bin/activate && pip
  install -r requirements.txt && python main.py`. PySide6 on macOS doesn't
  need any of the X11/Docker complexity in the first place - this is
  actually the simpler path on that OS specifically.
