$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
  npm install
}

if (-not (Test-Path ".env.local")) {
  Write-Host "frontend/.env.local not found. Browser API requests will infer http://<current-host>:8000." -ForegroundColor Yellow
}

$FrontendHost = if ([string]::IsNullOrWhiteSpace($env:FRONTEND_HOST)) { "0.0.0.0" } else { $env:FRONTEND_HOST }
$FrontendPort = if ([string]::IsNullOrWhiteSpace($env:FRONTEND_PORT)) { "3000" } else { $env:FRONTEND_PORT }

npm exec next dev -- --hostname $FrontendHost --port $FrontendPort
