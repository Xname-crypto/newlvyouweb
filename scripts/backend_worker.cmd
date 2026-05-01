@echo off
cd /d G:\newlvyouweb\backend
G:\newlvyouweb\backend\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --noreload 1>>G:\newlvyouweb\.codex-logs\backend.log 2>>G:\newlvyouweb\.codex-logs\backend.err.log
