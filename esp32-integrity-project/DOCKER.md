# Docker quick start (whole project)

One `docker-compose.yml` at this level drives both the firmware toolchain
and the dashboard. Layout it expects:
```
docker-compose.yml   <- this file's sibling
.env.example          <- copy to .env and adjust (port, display)
firmware/
dashboard/
```

## Prerequisites (Linux)

```
sudo apt install docker.io docker-compose-v2 x11-xserver-utils
sudo usermod -aG docker $USER   # log out/in afterward
cp .env.example .env            # then edit PORT/DISPLAY if needed
```

## Everyday commands

```
# Dashboard, Simulation Mode - no hardware, no extra setup beyond xhost:
xhost +local:docker
docker compose up --build dashboard

# Firmware: build (lean, ESP32-only image - recommended if you only target esp32)
docker compose run --rm firmware-build-slim

# ...or the official multi-chip image, if you'll target other ESP32 variants too
docker compose run --rm firmware-build

# Firmware: flash, monitor, menuconfig - each has a matching -slim variant
docker compose run --rm firmware-flash-slim
docker compose run --rm firmware-monitor-slim
docker compose run --rm firmware-menuconfig-slim
docker compose run --rm firmware-shell-slim

# Dashboard against a real board (X11 + serial device together)
xhost +local:docker
docker compose run --rm dashboard-hw

# Build a standalone Linux executable (no Python needed to run it)
docker compose build dashboard-package-linux
docker compose run --rm dashboard-package-linux
# -> dashboard/dist/FirmwareIntegrityMonitor/FirmwareIntegrityMonitor
# Windows executable needs an actual Windows machine - see dashboard/PACKAGING.md
```

**Stick to either all `-slim` or all non-`-slim` commands within one
project checkout.** Both point at the same bind-mounted `./firmware`
folder and produce the same `build/` output, so mixing them works
functionally - but it means Docker ends up with two large images
(`esp32-idf-slim` *and* `espressif/idf`) instead of one, which defeats
the point of choosing `-slim` in the first place.

`PORT` defaults to `/dev/ttyUSB0` - override per-command if yours differs:
```
PORT=/dev/ttyACM0 docker compose run --rm firmware-flash
```
(or set it once in `.env` instead of repeating it every time.)

**Why `docker compose up` alone only starts the dashboard:** every other
service needs a board plugged in, and Compose fails hard at startup if a
service's mapped device path doesn't exist. Keeping those as explicit,
named `run` commands means "no board attached" only breaks the command
that actually needed one, not everything.

## Ownership note (firmware)

The ESP-IDF image runs as root by default (Espressif's own documented
pattern), so `firmware/build/` will show up root-owned on your host. Fine
to read/reflash; if you need to delete or edit it as your normal user:
```
sudo chown -R "$(id -u):$(id -g)" firmware/build/
```

## Keeping this small on disk

Two real wins, plus general hygiene:

**1. Dashboard image is already leaner** - `requirements.txt` now installs
`PySide6-Essentials` instead of the full `PySide6` metapackage, which
otherwise drags in `PySide6-Addons` (QtWebEngine, QtMultimedia, Qt3D,
QtCharts, QtPdf, QtBluetooth...) that this app never imports. Several
hundred MB gone for zero functionality lost - nothing you need to do,
already reflected in the Dockerfile/requirements.

**2. Firmware: use the slim, ESP32-only image instead of the official one**
```
docker compose run --rm firmware-build-slim
```
The official `espressif/idf:v5.3.1` image bundles toolchains for every
supported chip (S2, S3, C2, C3, C6, H2, ...), not just the classic ESP32.
`firmware-build-slim` builds its own image
(`firmware/docker/Dockerfile.slim`) with only the ESP32 toolchain -
smaller, at the cost of a one-time `docker build` (a shallow, single-target
ESP-IDF clone - same resilient settings that fixed the earlier HTTP/2
clone issue are baked in). After that first build, it's cached and reuses
just like the official image does. If you ever need a different chip
later, either add its target to that Dockerfile or fall back to the plain
`firmware-build` service, which already supports any target.

*I can't tell you an exact size difference* - no Docker in the environment
that generated this project to measure it - but the official image commonly
runs several GB precisely because of the all-chips bundling, so the
single-target build should be meaningfully smaller. Compare for yourself:
```
docker compose build firmware-build-slim
docker images | grep -E "espressif/idf|esp32-idf-slim"
```

**3. General cleanup, once you've built a few times:**
```
docker system df                 # see what's actually using space, by category
docker builder prune             # clear stale build cache (this grows quietly)
docker image prune -a            # remove any images no container is using
docker volume rm esp32-integrity-project_idf-ccache   # wipe the ccache volume if it's grown large
```
`CCACHE_MAXSIZE=2G` is already set on the build services above, so the
ccache volume caps itself rather than growing unbounded across many builds
- raise or lower it in `docker-compose.yml` if you want a different limit.



Same caveats as before, just point the commands at this root file instead
of a per-project one:
- **Windows/WSL2**: attach the board via `usbipd` first (device
  passthrough), and point `DISPLAY` at your Windows X server for the
  dashboard's window. Full steps: `firmware/VM_TESTING.md` (device) and
  `dashboard/DOCKER.md` (X11/WSL2 specifics).
- **macOS**: Docker Desktop has no USB passthrough at all. `firmware-build`
  and `dashboard` (Simulation Mode) work fine through Docker; anything
  needing real hardware (`firmware-flash`, `firmware-monitor`,
  `dashboard-hw`) needs a native install on Mac instead.

## If you'd rather keep the two projects fully independent

The per-project setup still works standalone if you ever split
`firmware/` and `dashboard/` back into separate locations - each still has
its own `Dockerfile`/scripts under `scripts/`, just without a
`docker-compose.yml` of its own anymore (this root file replaces both).
To restore a standalone one, copy the relevant `firmware-*` or
`dashboard*` service block out of this file into its own
`docker-compose.yml` inside that project's folder.
