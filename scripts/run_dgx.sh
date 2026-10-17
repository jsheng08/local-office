#!/usr/bin/env bash
# Run Local Office directly on the DGX (no Mac, no tunnel).
# vLLM is already listening on 127.0.0.1:9000/9001/9006 on this host.
# The built Nuxt SPA (apps/web/.output/public) is served by FastAPI at http://localhost:8000.
set -euo pipefail
cd "$(dirname "$0")/.."

for port in 9000 9001 9006; do
  if curl -s -m 3 "http://127.0.0.1:${port}/v1/models" >/dev/null; then
    echo "model endpoint :${port} ok"
  else
    echo "model endpoint :${port} NOT reachable" >&2
  fi
done

if [ ! -f apps/web/.output/public/index.html ]; then
  echo "warning: apps/web/.output/public missing; build it with 'npm run generate' in apps/web and copy it here" >&2
fi

exec .venv/bin/uvicorn apps.api.main:app --host 127.0.0.1 --port "${PORT:-8000}"
