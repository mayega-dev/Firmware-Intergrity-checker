#!/usr/bin/env bash
# Interactive menuconfig (e.g. to set ALERT_UART_PORT_NUM / TX / RX pins,
# or disable console output for the single-cable test setup).
# Usage: ./scripts/docker-menuconfig.sh
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm -it \
    -v "$PWD":/project \
    -w /project \
    espressif/idf:v5.3.1 \
    idf.py menuconfig
