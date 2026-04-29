@echo off
echo Stopping Bambu Lab Dashboard server...
if not exist server.pid goto nokill
set /p PID=<server.pid
taskkill /pid %PID% /f >nul 2>&1
del server.pid
echo Server stopped.
goto end
:nokill
echo No server.pid found. Stopping all node.exe processes...
taskkill /im node.exe /f >nul 2>&1
echo Done.
:end
timeout /t 2 >nul
