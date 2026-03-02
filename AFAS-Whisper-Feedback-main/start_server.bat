@echo off
REM Script to start AFAS server
cd /d "%~dp0AFAS-Whisper-Feedback-main"
echo Starting AFAS server...
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
pause

