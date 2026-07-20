#!/usr/bin/env bash
set -euo pipefail

SERVICE="${SERVICE:-cowrie}"
TARGET_HOST="${TARGET_HOST:-1.1.1.1}"
TARGET_PORT="${TARGET_PORT:-80}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-3}"
PYTHON_PATH="${PYTHON_PATH:-/cowrie/cowrie-env/bin/python3}"

echo "Checking outbound connectivity from service '${SERVICE}' to ${TARGET_HOST}:${TARGET_PORT}"

python_script=$(cat <<PY
import socket
import sys

target_host = "${TARGET_HOST}"
target_port = int("${TARGET_PORT}")
timeout = int("${TIMEOUT_SECONDS}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(timeout)
try:
    sock.connect((target_host, target_port))
except OSError:
    sys.exit(0)
else:
    sys.exit(1)
finally:
    sock.close()
PY
)

set +e
printf '%s' "${python_script}" | docker compose exec -T "${SERVICE}" "${PYTHON_PATH}" -
status=$?
set -e

if [ "${status}" -eq 0 ]; then
    echo "OK: outbound connection was blocked."
    exit 0
fi

if [ "${status}" -eq 1 ]; then
    echo "NG: outbound connection succeeded. Review Docker network or firewall settings." >&2
    exit 1
fi

exit "${status}"
