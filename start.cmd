@echo off
rem IT-testare - starta pa Windows (dubbelklicka).
cd /d "%~dp0"
start "" http://127.0.0.1:8765
".venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8765
