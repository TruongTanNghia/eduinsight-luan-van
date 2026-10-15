@echo off
cd /d %~dp0\..
python -X utf8 -W ignore experiments\run_benchmark.py %*
pause
