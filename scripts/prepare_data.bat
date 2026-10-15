@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -X utf8 -m e3m.data
pause
