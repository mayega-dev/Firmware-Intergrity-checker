#!/usr/bin/env bash
# Flash the built firmware to a real board over USB.
# Usage: ./scripts/docker-flash.sh [/dev/ttyUSB0]
#
# Linux only as written (native device passthrough). On Windows/WSL2, first
# attach the board via usbipd (see ../VM_TESTING.md), then run this same
# script from inside the WSL2 shell - /dev/ttyUSB0 will exist there too.
# macOS: Docker Desktop doesn't support USB device passthrough at all -
# install ESP-IDF natively instead for flashing on Mac.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-/dev/ttyUSB0}"

if [ ! -e "$PORT" ]; then
    echo "Error: $PORT does not exist. Is the board plugged in?" >&2
    echo "Check with: ls /dev/ttyUSB* /dev/ttyACM*" >&2
    exit 1
fi

docker run --rm -it \
    --device="$PORT":"$PORT" \
    -v "$PWD":/project \
    -w /project \
    espressif/idf:v5.3.1 \
    idf.py -p "$PORT" flash
