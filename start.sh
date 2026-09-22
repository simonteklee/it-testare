#!/usr/bin/env bash
# IT-testare — startar servern (om den inte redan kör) och öppnar webbläsaren.
set -e
cd "$(dirname "$0")"
PORT=8765
if ! curl -s -m 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
  nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >/tmp/it-testare.log 2>&1 &
  for i in $(seq 1 20); do
    curl -s -m 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
    sleep 0.5
  done
fi
xdg-open "http://127.0.0.1:$PORT" >/dev/null 2>&1 &
