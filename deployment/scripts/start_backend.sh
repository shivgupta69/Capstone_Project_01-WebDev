#!/usr/bin/env bash
set -e

find_free_port() {
  local port="$1"
  while lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
    port=$((port + 1))
  done
  echo "$port"
}

if [ -z "${PORT:-}" ]; then
  PORT="$(find_free_port 5000)"
  export PORT
else
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Error: PORT=$PORT is already in use. Choose another port, for example:"
    echo "  PORT=5001 bash deployment/scripts/start_backend.sh"
    exit 1
  fi
fi

python -m backend.scripts.init_db
echo "Starting app on http://localhost:$PORT"
exec python -m gunicorn -c deployment/gunicorn.conf.py backend.run:app
