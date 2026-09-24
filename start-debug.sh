#!/usr/bin/env bash
# TestARN — felläge: startar servern i förgrunden så att fel blir synliga.
# Kor: ./start-debug.sh   (stoppa med Ctrl+C)
cd "$(dirname "$0")"
echo "Startar TestARN i forgrunden. Fel visas har nedan. Stoppa med Ctrl+C."
echo "-------------------------------------------------------------"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765
