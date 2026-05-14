$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendScript = Join-Path $PSScriptRoot "dev-backend.ps1"
$FrontendScript = Join-Path $PSScriptRoot "dev-frontend.ps1"

Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", $BackendScript -WorkingDirectory $Root
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", $FrontendScript -WorkingDirectory $Root

Write-Host "Backend and frontend startup windows have been opened."
