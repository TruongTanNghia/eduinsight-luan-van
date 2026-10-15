@echo off
cd /d %~dp0\..
uvicorn backend.main:app --host 127.0.0.1 --port 8010
