@echo off
setlocal

set "ROOT=G:\newlvyouweb"
set "BACKEND=%ROOT%\backend"
set "LOGDIR=%ROOT%\.codex-logs"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

start "newlvyouweb-backend" /min cmd /c G:\newlvyouweb\scripts\backend_worker_127.cmd

echo Backend start requested on http://127.0.0.1:8000
