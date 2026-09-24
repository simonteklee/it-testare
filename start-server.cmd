@echo off
rem TestARN - startar servern och loggar till testarn.log (Windows).
rem Kor Python direkt (via -m uvicorn) for att undvika uv:s .exe-trampoliner.
cd /d "%~dp0"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8765 > "testarn.log" 2>&1
