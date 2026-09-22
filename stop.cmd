@echo off
rem IT-testare - stoppa servern (Windows).
taskkill /IM uvicorn.exe /F >nul 2>&1
echo IT-testare stoppad.
timeout /t 2 >nul
