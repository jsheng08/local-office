#!/usr/bin/env bash
# Report served model identities and one measured Lightning completion. No installs.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

for port in 9000 9001 9006; do
  echo "== localhost:${port}/v1/models =="
  curl --noproxy '*' -fsS --connect-timeout 3 --max-time 10 \
    "http://127.0.0.1:${port}/v1/models" -o "$work_dir/models-${port}.json"
  "$PYTHON" - "$work_dir/models-${port}.json" <<'PY'
import json, sys
models = json.load(open(sys.argv[1]))["data"]
if not models:
    raise SystemExit("ERROR: no models served")
for model in models:
    print("id=%s  root=%s" % (model["id"], model.get("root", "(not reported)")))
PY
done

"$PYTHON" - "$work_dir/models-9000.json" "$work_dir/request.json" <<'PY'
import json, sys
model = json.load(open(sys.argv[1]))["data"][0]["id"]
with open(sys.argv[2], "w") as target:
    json.dump({"model": model, "messages": [{"role": "user", "content": "Reply with OK."}],
               "max_tokens": 16, "temperature": 0,
               "chat_template_kwargs": {"enable_thinking": False}}, target)
PY
echo '== Lightning: one real call, enable_thinking=false =='
curl --noproxy '*' -fsS --connect-timeout 3 --max-time 120 \
  -H 'Content-Type: application/json' --data-binary "@$work_dir/request.json" \
  -o "$work_dir/answer.json" -w 'end_to_end_seconds=%{time_total}\n' \
  http://127.0.0.1:9000/v1/chat/completions
"$PYTHON" - "$work_dir/answer.json" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
content = body["choices"][0]["message"].get("content")
print("answer=%r usage=%s" % (content, body.get("usage")))
if not content:
    raise SystemExit("ERROR: model returned no visible answer")
PY
