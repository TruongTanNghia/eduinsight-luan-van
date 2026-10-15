@echo off
cd /d %~dp0\..
streamlit run apps\thesis_dashboard\app.py --server.port 8501
