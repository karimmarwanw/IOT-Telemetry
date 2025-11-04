@echo off
set DURATION=60

echo Starting server...
start /B python server.py

timeout /t 1 >nul

echo Starting client...
start /B python client.py

echo Running test for %DURATION% seconds...
timeout /t %DURATION% >nul

echo Stopping processes...
taskkill /IM python.exe /F >nul 2>&1

echo Test finished.
pause