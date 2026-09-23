#!/usr/bin/env bash
# Drop into an interactive shell inside the build container, with the
# ESP-IDF environment already sourced (idf.py, esptool.py, etc. all on
# PATH). Useful for anything not covered by the other scripts.
# Usage: ./scripts/docker-shell.sh [/dev/ttyUSB0]
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-/dev/ttyUSB0}"
DEVICE_ARGS=()
if [ -e "$PORT" ]; then
    DEVICE_ARGS=(--device="$PORT":"$PORT")
else
    echo "Note: $PORT not found - starting without device passthrough (build-only)." >&2
fi

docker run --rm -it \
    "${DEVICE_ARGS[@]}" \
    -v "$PWD":/project \
    -w /project \
    espressif/idf:v5.3.1 \
    bash
