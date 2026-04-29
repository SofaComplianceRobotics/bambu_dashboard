@echo off
title Bambu Lab Dashboard
echo.
echo  ================================================
echo   Bambu Lab Print Farm Dashboard
echo  ================================================
echo.
cd /d "%~dp0"
set "NODE_DIR=%~dp0..\nodejs"
set "NODE=%NODE_DIR%\node.exe"
set "NPM=%NODE_DIR%\npm.cmd"
if not exist "%NODE%" (
    echo Portable nodejs not found, trying system Node...
    set "NODE=node"
    set "NPM=npm"
    set "NODE_DIR="
)
if defined NODE_DIR set "PATH=%NODE_DIR%;%PATH%"
if not exist "node_modules" (
    echo Installing dependencies...
    "%NPM%" install
)
echo Starting server in background...
powershell -Command "$p = Start-Process -FilePath '%NODE%' -ArgumentList 'server.js' -WorkingDirectory '%CD%' -WindowStyle Hidden -RedirectStandardOutput '%CD%\server.log' -RedirectStandardError '%CD%\server.err' -PassThru; $p.Id | Set-Content '%CD%\server.pid'"
echo Opening dashboard...
timeout /t 2 >nul
start dashboard.html
echo.
echo  Server running silently. Run stop_dashboard.bat to stop it.
timeout /t 4 >nul