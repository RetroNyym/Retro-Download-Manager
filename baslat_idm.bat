@echo off
setlocal
cd /d "%~dp0"

set "PYW=%LOCALAPPDATA%\Python\pythoncore-3.14-64\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw.exe"
if not exist "%PYW%" set "PYW=python.exe"

start "" "%PYW%" -m download_manager
endlocal
