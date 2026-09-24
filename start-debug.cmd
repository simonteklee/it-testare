@echo off
rem TestARN - fellage: startar servern i forgrunden sa att fel blir synliga.
cd /d "%~dp0"
echo Startar TestARN i forgrunden. Fel visas nedan. Stoppa med Ctrl+C.
echo -------------------------------------------------------------
".venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8765
echo.
echo -------------------------------------------------------------
echo Servern avslutades. Skicka texten ovan till Simon.
pause
