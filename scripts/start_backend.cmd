@echo off
if not exist "G:\newlvyouweb\.codex-logs" mkdir "G:\newlvyouweb\.codex-logs"
start "" /b cmd /c G:\newlvyouweb\scripts\backend_worker.cmd
