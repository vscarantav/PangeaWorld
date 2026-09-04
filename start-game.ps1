[CmdletBinding()]
param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 5173
)

$projectRoot = $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$frontendRoot = Join-Path $projectRoot 'frontend'
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment not found at $python"
}

$backendProcess = $null
$frontendProcess = $null
$previousViteApiUrl = $env:VITE_API_URL

try {
    Write-Host "Starting PangeaWorld backend on http://localhost:$BackendPort ..." -ForegroundColor Cyan
    $backendProcess = Start-Process -FilePath $python `
        -ArgumentList "-m uvicorn backend.main:app --port $BackendPort" `
        -WorkingDirectory $projectRoot -PassThru

    Write-Host "Starting PangeaWorld frontend on http://localhost:$FrontendPort ..." -ForegroundColor Cyan
    # Windows PowerShell 5.1 has no Start-Process -Environment parameter.
    $env:VITE_API_URL = "http://localhost:$BackendPort"
    $frontendProcess = Start-Process -FilePath 'npm.cmd' `
        -ArgumentList "run dev -- --host localhost --port $FrontendPort" `
        -WorkingDirectory $frontendRoot `
        -PassThru
    $env:VITE_API_URL = $previousViteApiUrl

    Write-Host ''
    Write-Host "Game:    http://localhost:$FrontendPort" -ForegroundColor Green
    Write-Host "API:     http://localhost:$BackendPort" -ForegroundColor Green
    Write-Host "Swagger: http://localhost:$BackendPort/docs" -ForegroundColor Green
    Write-Host ''
    Write-Host 'Press Ctrl+C here to stop both servers.' -ForegroundColor Yellow

    while (-not $frontendProcess.HasExited -and -not $backendProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
}
finally {
    foreach ($process in @($frontendProcess, $backendProcess)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host 'PangeaWorld servers stopped.' -ForegroundColor Yellow
}
