#!/bin/bash
# Sources the ESP-IDF environment (puts idf.py, esptool.py, the compiler,
# etc. on PATH) before running whatever command was passed to `docker run`.
set -e
# shellcheck disable=SC1091
source "$IDF_PATH/export.sh" > /dev/null
exec "$@"
