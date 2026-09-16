Write-Host "Starting SIH26093 FastAPI Backend on http://0.0.0.0:8000 ..." -ForegroundColor Cyan
Set-Location -Path "\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
