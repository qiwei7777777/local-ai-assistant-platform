$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

Write-Host "[1/4] Installing backend test dependencies..."
Set-Location $Root
Set-Location (Join-Path $Root "backend")
python -m pip install -e ".[dev]"

Write-Host "[2/5] Running Python tests..."
Set-Location $Root
python -m unittest discover -s tests -p "test_*.py"

Write-Host "[3/5] Installing frontend dependencies..."
Set-Location (Join-Path $Root "frontend")
npm install

Write-Host "[4/5] Building frontend..."
npm run build

Write-Host "[5/5] Validating backend health endpoint..."
try {
  $BackendBaseUrl = if ([string]::IsNullOrWhiteSpace($env:SMOKE_TEST_BACKEND_URL)) { "http://127.0.0.1:8000" } else { $env:SMOKE_TEST_BACKEND_URL }
  $health = Invoke-WebRequest -UseBasicParsing "$BackendBaseUrl/api/health"
  Write-Host $health.Content
} catch {
  Write-Warning "Backend is not running or health endpoint is unavailable."
}

Write-Host "[4/4] Smoke test finished."
