@echo off
cd /d %~dp0
start "EduInsight API" cmd /k run_api.bat
start "EduInsight Web" cmd /k run_web.bat
timeout /t 8 >nul
start http://localhost:3005/dashboard
