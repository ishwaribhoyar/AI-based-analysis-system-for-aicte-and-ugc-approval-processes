# PowerShell script to start the backend server
Write-Host "Starting Smart Approval AI Backend Server..." -ForegroundColor Green
Write-Host ""

$backendPath = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backendPath)) {
    Write-Host "Error: Backend directory not found at $backendPath" -ForegroundColor Red
    exit 1
}

Set-Location $backendPath

# Check if virtual environment exists
$venvPath = Join-Path $backendPath "venv"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

# Check if uvicorn is available
try {
    python -c "import uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: uvicorn not installed. Please run: pip install -r requirements.txt" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Python not found or uvicorn not installed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
