FROM python:3.11-slim

# System libraries required for PySide6's "xcb" Qt platform plugin to
# initialize at all. Missing any of these typically shows up as:
#   "qt.qpa.plugin: Could not load the Qt platform plugin 'xcb'"
# python:3.11-slim has none of this by default (it's a headless base
# image), so it all has to be added explicitly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libfontconfig1 \
    libfreetype6 \
    libx11-xcb1 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxrender1 \
    libxi6 \
    libsm6 \
    libice6 \
    libdbus-1-3 \
    libglib2.0-0 \
    fonts-noto-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first, separately from app code, so `docker build`
# doesn't reinstall PySide6 (the slow part) every time a .py file changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 180 --retries 15 -r requirements.txt

COPY . .

# Serial port access as a non-root user needs the `dialout` group; running
# as root sidesteps that entirely and matches the same pattern used for
# the firmware build container - simplest thing that reliably works.
CMD ["python3", "main.py"]
