#!/usr/bin/env bash
# Build the firmware inside Docker - no local ESP-IDF install required.
# Usage: ./scripts/docker-build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose run --rm idf
