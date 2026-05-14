$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"

Set-Location $BackendDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

if (Test-Path "..\\.env") {
  Write-Host "Project-root .env detected and will be loaded by backend settings." -ForegroundColor Cyan
}

$BackendHost = if ([string]::IsNullOrWhiteSpace($env:APP_HOST)) { "0.0.0.0" } else { $env:APP_HOST }
$BackendPort = if ([string]::IsNullOrWhiteSpace($env:APP_PORT)) { "8000" } else { $env:APP_PORT }

& ".\.venv\Scripts\python.exe" -m pip install -e .
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host $BackendHost --port $BackendPort
