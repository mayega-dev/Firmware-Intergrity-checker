#!/usr/bin/env bash
# View live console/log output (only useful if you kept the console enabled
# - i.e. the two-cable setup. In the single-cable quick-test config from
# earlier, the console is disabled and this will show nothing; use the
# dashboard app instead to see device output in that configuration).
# Usage: ./scripts/docker-monitor.sh [/dev/ttyUSB0]
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-/dev/ttyUSB0}"

if [ ! -e "$PORT" ]; then
    echo "Error: $PORT does not exist. Is the board plugged in?" >&2
    exit 1
fi

docker run --rm -it \
    --device="$PORT":"$PORT" \
    -v "$PWD":/project \
    -w /project \
    espressif/idf:v5.3.1 \
    idf.py -p "$PORT" monitor
