@echo off
setlocal EnableExtensions
set DURATION=60

cd /d "%~dp0"

rem choose interpreter
set "PY=py"
%PY% -c "print(1)" >nul 2>&1 || set "PY=python"

echo Starting server...
start "UDP_SERVER" /min %PY% server.py

timeout /t 1 /nobreak >nul

echo Starting client...
start "UDP_CLIENT" /min %PY% client.py

echo Running test for %DURATION% seconds...
timeout /t %DURATION% /nobreak >nul

echo Stopping processes...
rem kill the exact two we started
taskkill /FI "WINDOWTITLE eq UDP_SERVER" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq UDP_CLIENT" /T /F >nul 2>&1

rem safety net: catch other python variants under this user
for /l %%I in (1,1,5) do (
  for %%N in (python.exe python3.exe pythonw.exe py.exe) do taskkill /FI "USERNAME eq %USERNAME%" /IM %%N /F >nul 2>&1
  tasklist /FI "USERNAME eq %USERNAME%" /FI "IMAGENAME eq python.exe"  | find /I "python.exe"  >nul && timeout /t 1 >nul && goto :continue
  tasklist /FI "USERNAME eq %USERNAME%" /FI "IMAGENAME eq python3.exe" | find /I "python3.exe" >nul && timeout /t 1 >nul && goto :continue
  goto :done
  :continue
)

:done
exit