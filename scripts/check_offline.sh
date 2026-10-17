#!/usr/bin/env bash
# REPORT ONLY: never adds/deletes routes, stops networking, or changes model services.
set -uo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

echo '== Mac default route (report only) =='
if command -v route >/dev/null 2>&1; then
  route -n get default 2>&1 || echo 'IPv4 default route absent or unreadable; inspect error above (permission denial means UNKNOWN).'
  route -n get -inet6 default 2>&1 || echo 'IPv6 default route absent or unreadable; inspect error above (permission denial means UNKNOWN).'
else
  echo 'route command unavailable; cannot determine Mac route.'
fi
echo '== Mac public HTTPS reachability (3 s; bypass proxy) =='
if curl --noproxy '*' -IsS --connect-timeout 3 --max-time 3 https://huggingface.co; then
  echo 'Mac: public HTTPS reachable.'
else
  echo 'Mac: public HTTPS request failed (does not alone prove offline operation).'
fi

echo '== DGX routes and public HTTPS reachability (report only) =='
ssh -o BatchMode=yes -o ConnectTimeout=3 -o ConnectionAttempts=1 Hackathonnode 'bash -s' <<'REMOTE'
echo 'IPv4 default routes:'
ip -4 route show default
echo 'IPv6 default routes:'
ip -6 route show default
if curl --noproxy '*' -IsS --connect-timeout 3 --max-time 3 https://huggingface.co; then
  echo 'DGX: public HTTPS reachable.'
else
  echo 'DGX: public HTTPS request failed (does not alone prove offline operation).'
fi
REMOTE
if [ "$?" -ne 0 ]; then
  echo 'DGX: SSH/report failed; remote connectivity status unknown.'
fi

echo '== Local models: real completion through the existing tunnel =='
failed=0
for port in 9000 9001 9006; do
  echo "localhost:${port}"
  if ! curl --noproxy '*' -fsS --connect-timeout 3 --max-time 10 \
    "http://127.0.0.1:${port}/v1/models" -o "$work_dir/models.json"; then
    echo 'FAIL: models endpoint unavailable'; failed=1; continue
  fi
  if ! "$PYTHON" - "$work_dir/models.json" "$work_dir/request.json" <<'PY'
import json, sys
model = json.load(open(sys.argv[1]))["data"][0]["id"]
print("served model: %s" % model)
with open(sys.argv[2], "w") as target:
    json.dump({"model": model, "messages": [{"role": "user", "content": "Reply with OK."}],
               "max_tokens": 16, "temperature": 0,
               "chat_template_kwargs": {"enable_thinking": False}}, target)
PY
  then
    echo 'FAIL: invalid model listing'; failed=1; continue
  fi
  if ! curl --noproxy '*' -fsS --connect-timeout 3 --max-time 120 \
    -H 'Content-Type: application/json' --data-binary "@$work_dir/request.json" \
    -o "$work_dir/answer.json" -w 'end_to_end_seconds=%{time_total}\n' \
    "http://127.0.0.1:${port}/v1/chat/completions"; then
    echo 'FAIL: local completion request failed'; failed=1; continue
  fi
  if ! "$PYTHON" - "$work_dir/answer.json" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
content = body["choices"][0]["message"].get("content")
print("answer=%r" % content)
if not content:
    raise SystemExit("FAIL: no visible model answer")
PY
  then
    failed=1
  fi
done
echo 'Report complete. Successful local calls with public internet reachable do not prove offline operation.'
exit "$failed"
