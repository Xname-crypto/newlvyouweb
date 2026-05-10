@echo off
cd /d G:\newlvyouweb\backend
G:\newlvyouweb\backend\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload 1>>G:\newlvyouweb\.codex-logs\backend-persistent.log 2>>G:\newlvyouweb\.codex-logs\backend-persistent.err.log
