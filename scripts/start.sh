#!/usr/bin/env bash
# Start the engine. Ctrl+C stops it.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

engine_url="http://127.0.0.1:8790"
started=()

up() {
  curl -sf -o /dev/null --max-time 2 "$1"
}

stop_pid() {
  local pid="$1"
  local child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    stop_pid "$child"
  done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  local pid
  for pid in "${started[@]}"; do
    stop_pid "$pid"
  done
}
trap cleanup EXIT INT TERM

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
if [[ ! -x .venv/bin/catalogmuse-engine && ! -x .venv/bin/catalogmuse ]]; then
  .venv/bin/pip install -e .
fi
if [[ ! -f .env.local ]] || ! grep -q '^MODEL_API_KEY=.' .env.local; then
  echo "Put MODEL_API_KEY in .env.local before starting." >&2
  exit 1
fi

if up "$engine_url/health"; then
  echo "Engine already running at $engine_url"
  trap - EXIT INT TERM
  exit 0
fi

python3 - "$root" <<'PY' &
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
os.chdir(root)
for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"):
    os.environ.pop(name, None)
key = ""
for line in (root / ".env.local").read_text().splitlines():
    if not line.startswith("MODEL_API_KEY="):
        continue
    key = line.split("=", 1)[1].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
        key = key[1:-1]
    break
if not key:
    sys.exit("MODEL_API_KEY is missing from .env.local")
os.environ["MODEL_API_KEY"] = key
os.environ["CATALOGMUSE_PORT"] = "8790"
binary = root / ".venv" / "bin" / "catalogmuse-engine"
if not binary.exists():
    binary = root / ".venv" / "bin" / "catalogmuse"
os.execv(str(binary), [str(binary)])
PY
started+=("$!")

for _ in $(seq 1 40); do
  if up "$engine_url/health"; then
    echo "Engine  $engine_url"
    echo "Press Ctrl+C to stop."
    while true; do
      for pid in "${started[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
          echo "The engine exited." >&2
          exit 1
        fi
      done
      sleep 1
    done
  fi
  for pid in "${started[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "The engine exited before it was ready." >&2
      exit 1
    fi
  done
  sleep 0.5
done

echo "The engine did not become ready." >&2
exit 1
