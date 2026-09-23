@echo off
rem TestARN - stoppa servern (Windows).
taskkill /IM uvicorn.exe /F >nul 2>&1
echo TestARN stoppad.
timeout /t 2 >nul
