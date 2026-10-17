#!/usr/bin/env bash
# Start Local Office: ensure SSH tunnel to the ATOM's vLLM ports, then run the API + web UI.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"

if curl -fsS -m 5 http://localhost:9000/v1/models >/dev/null 2>&1; then
  echo "[run] tunnel up (localhost:9000 reachable)"
else
  echo "[run] tunnel down, starting SSH tunnel to Hackathonnode..."
  ssh -fN -o ServerAliveInterval=15 -o ExitOnForwardFailure=yes \
    -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 -L 9006:127.0.0.1:9006 Hackathonnode
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS -m 5 http://localhost:9000/v1/models >/dev/null 2>&1; then
      echo "[run] tunnel up"; break
    fi
    sleep 1
  done
  curl -fsS -m 5 http://localhost:9000/v1/models >/dev/null 2>&1 || { echo "[run] ERROR: local Nemotron endpoint unreachable on :9000" >&2; exit 1; }
fi

exec .venv/bin/uvicorn apps.api.main:app --host 127.0.0.1 --port "$PORT"
