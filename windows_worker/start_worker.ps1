# Windows Agent Worker startup script for PowerShell
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to project root to allow standard module imports (e.g. windows_worker.worker)
Set-Location -Path $scriptDir\..

Write-Host "Checking configurations..." -ForegroundColor Cyan

$envFile = "$scriptDir\.env.windows"
$envExample = "$scriptDir\.env.windows.example"

if (-not (Test-Path $envFile)) {
    Write-Host ".env.windows not found! Copying from .env.windows.example..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
}

# Get Host/Port settings from .env.windows or fallback to defaults
$hostIp = "127.0.0.1"
$port = "9100"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^WINDOWS_WORKER_HOST=(.+)$") {
            $hostIp = $Matches[1].Trim()
        }
        if ($_ -match "^WINDOWS_WORKER_PORT=(.+)$") {
            $port = $Matches[1].Trim()
        }
    }
}

Write-Host "Starting worker on http://$hostIp`:$port..." -ForegroundColor Green
python -m uvicorn windows_worker.worker:app --host $hostIp --port $port --reload
