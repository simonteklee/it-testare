@echo off
rem TestARN - startar servern och loggar till testarn.log (Windows).
cd /d "%~dp0"
".venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8765 > "testarn.log" 2>&1
