#!/usr/bin/env bash
# TestARN — startar servern (om den inte redan kör) och öppnar webbläsaren.
set -e
cd "$(dirname "$0")"
PORT=8765
H="http://127.0.0.1:$PORT/api/health"

if ! curl -s -m 2 "$H" >/dev/null 2>&1; then
  nohup .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >/tmp/testarn.log 2>&1 &
  for _ in $(seq 1 30); do
    curl -s -m 2 "$H" >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

# Om servern fortfarande inte svarar: visa felet istallet for en tom sida.
if ! curl -s -m 2 "$H" >/dev/null 2>&1; then
  echo "! TestARN-servern startade inte pa http://127.0.0.1:$PORT"
  echo "  Senaste logg (/tmp/testarn.log):"
  echo "  ------------------------------------------------------------"
  tail -n 20 /tmp/testarn.log 2>/dev/null || echo "  (ingen logg hittades)"
  echo "  ------------------------------------------------------------"
  echo "  Kor './start-debug.sh' for att se hela felet."
  exit 1
fi

for b in brave-origin-stable brave-browser brave chromium chromium-browser google-chrome; do
  if command -v "$b" >/dev/null 2>&1; then
    "$b" --app="http://127.0.0.1:$PORT" >/dev/null 2>&1 &
    exit 0
  fi
done
xdg-open "http://127.0.0.1:$PORT" >/dev/null 2>&1 &
