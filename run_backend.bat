@echo off
echo Starting SIH26093 FastAPI Backend on http://0.0.0.0:8000 ...
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
