@echo off
cd /d %~dp0\..
streamlit run apps\student_analytics\app.py --server.port 8502
