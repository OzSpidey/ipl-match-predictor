# IPL Predictor — one-shot setup & launch script
# Run from the ipl-predictor/ directory: .\run.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n🏏  IPL Match Predictor — Setup & Launch" -ForegroundColor Cyan

# ── Python env ────────────────────────────────────────────────────────────────
if (-not (Test-Path "venv")) {
    Write-Host "[1/5] Creating Python virtual environment…" -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[2/5] Installing Python dependencies…" -ForegroundColor Yellow
& .\venv\Scripts\pip install -r requirements.txt --quiet

# ── Data ──────────────────────────────────────────────────────────────────────
Write-Host "[3/5] Generating IPL dataset…" -ForegroundColor Yellow
& .\venv\Scripts\python generate_data.py

# ── Train ─────────────────────────────────────────────────────────────────────
Write-Host "[4/5] Training models (may take ~60s)…" -ForegroundColor Yellow
& .\venv\Scripts\python train.py

# ── Frontend ──────────────────────────────────────────────────────────────────
Write-Host "[5/5] Installing frontend dependencies…" -ForegroundColor Yellow
Push-Location frontend
npm install --silent
Pop-Location

Write-Host "`n✅  Setup complete!" -ForegroundColor Green
Write-Host "Starting API server on http://localhost:8000 …" -ForegroundColor Cyan
Write-Host "Starting UI  on http://localhost:3000 …" -ForegroundColor Cyan
Write-Host "(Press Ctrl+C to stop both)`n" -ForegroundColor Gray

# Launch API in background
$api = Start-Process -FilePath ".\venv\Scripts\uvicorn" `
    -ArgumentList "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
    -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 2

# Launch frontend (blocking)
Push-Location frontend
npm run dev
Pop-Location

$api | Stop-Process -Force
