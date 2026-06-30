#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://localhost:5000/login}"

echo "Checking connectivity to ${TARGET_URL}"
curl --fail --silent --show-error --head "${TARGET_URL}"
