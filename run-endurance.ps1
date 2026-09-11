[CmdletBinding()]
param(
    [ValidateRange(1, 1440)]
    [int]$DurationMinutes = 30,
    [ValidateRange(0, 3600)]
    [int]$PauseSeconds = 0,
    [ValidateRange(0, 100000)]
    [int]$MaxIterations = 0,
    [switch]$IncludeBrowser,
    [string]$OutputDirectory
)

# Repeated local verification for PangeaWorld. Each iteration uses the full
# API regression suite, frontend tests, lint, and production build. Browser
# coverage is opt-in because it is much slower and requires Chrome.

# Native tools write warnings and server diagnostics to stderr even when they
# exit successfully. Suppress PowerShell's duplicate red ErrorRecord display;
# Invoke-LoggedCommand still captures that output in each command log and uses
# the native exit code to decide whether an iteration passed.
$ErrorActionPreference = 'SilentlyContinue'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$frontendRoot = Join-Path $projectRoot 'frontend'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment not found at $python"
}

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $OutputDirectory = Join-Path $projectRoot "endurance-logs\$stamp"
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$outcomeLog = Join-Path $OutputDirectory 'outcomes.jsonl'
$summaryLog = Join-Path $OutputDirectory 'summary.txt'
$deadline = (Get-Date).AddMinutes($DurationMinutes)

function Invoke-LoggedCommand {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$LogPath,
        [scriptblock]$Command
    )

    Push-Location $WorkingDirectory
    try {
        Write-Host "[$Name] running..." -ForegroundColor DarkCyan
        # Out-Host prevents Tee-Object's captured console lines from becoming
        # this function's return value; callers receive only the native exit
        # code while still seeing and saving the complete command output.
        & $Command *>&1 | Tee-Object -FilePath $LogPath | Out-Host
        return [int]$LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

"PangeaWorld endurance run started $(Get-Date -Format o)" | Set-Content $summaryLog
"Output directory: $OutputDirectory" | Add-Content $summaryLog
"Duration: $DurationMinutes minutes; browser: $IncludeBrowser" | Add-Content $summaryLog

$iteration = 0
$passed = 0
$failed = 0
while ((Get-Date) -lt $deadline -and ($MaxIterations -eq 0 -or $iteration -lt $MaxIterations)) {
    $iteration += 1
    $iterationStarted = Get-Date
    $iterationDirectory = Join-Path $OutputDirectory ("iteration-{0:D4}" -f $iteration)
    New-Item -ItemType Directory -Force -Path $iterationDirectory | Out-Null

    $backendExit = Invoke-LoggedCommand -Name 'backend' -WorkingDirectory (Join-Path $projectRoot 'backend') `
        -LogPath (Join-Path $iterationDirectory 'backend.log') `
        -Command { & $python -m pytest tests -q --junitxml (Join-Path $iterationDirectory 'backend-junit.xml') }
    $frontendTestExit = Invoke-LoggedCommand -Name 'frontend-test' -WorkingDirectory $frontendRoot `
        -LogPath (Join-Path $iterationDirectory 'frontend-test.log') -Command { & npm.cmd test }
    $frontendLintExit = Invoke-LoggedCommand -Name 'frontend-lint' -WorkingDirectory $frontendRoot `
        -LogPath (Join-Path $iterationDirectory 'frontend-lint.log') -Command { & npm.cmd run lint }
    $frontendBuildExit = Invoke-LoggedCommand -Name 'frontend-build' -WorkingDirectory $frontendRoot `
        -LogPath (Join-Path $iterationDirectory 'frontend-build.log') -Command { & npm.cmd run build }

    $browserExit = $null
    if ($IncludeBrowser) {
        # Use unique ports per iteration so a server left behind by an
        # interrupted Playwright run cannot block the next one.
        $env:E2E_BACKEND_PORT = 8100 + ($iteration % 500)
        $env:E2E_FRONTEND_PORT = 5200 + ($iteration % 500)
        # Isolate both data and traces. This makes a failed iteration
        # self-contained even when Windows later recycles a process ID.
        $env:E2E_RUN_ID = [guid]::NewGuid().ToString('N')
        $env:E2E_ARTIFACT_DIR = Join-Path $iterationDirectory 'playwright'
        $browserExit = Invoke-LoggedCommand -Name 'browser' -WorkingDirectory $frontendRoot `
            -LogPath (Join-Path $iterationDirectory 'browser.log') -Command { & npm.cmd run test:e2e }
        Remove-Item Env:E2E_BACKEND_PORT -ErrorAction SilentlyContinue
        Remove-Item Env:E2E_FRONTEND_PORT -ErrorAction SilentlyContinue
        Remove-Item Env:E2E_RUN_ID -ErrorAction SilentlyContinue
        Remove-Item Env:E2E_ARTIFACT_DIR -ErrorAction SilentlyContinue
    }

    $allExitCodes = @($backendExit, $frontendTestExit, $frontendLintExit, $frontendBuildExit)
    if ($null -ne $browserExit) { $allExitCodes += $browserExit }
    $status = if ($allExitCodes | Where-Object { $_ -ne 0 }) { 'failed' } else { 'passed' }
    if ($status -eq 'passed') { $passed += 1 } else { $failed += 1 }

    $record = [ordered]@{
        iteration = $iteration
        started_at = $iterationStarted.ToString('o')
        finished_at = (Get-Date).ToString('o')
        status = $status
        backend_exit = [int]$backendExit
        frontend_test_exit = [int]$frontendTestExit
        frontend_lint_exit = [int]$frontendLintExit
        frontend_build_exit = [int]$frontendBuildExit
        browser_exit = if ($null -eq $browserExit) { $null } else { [int]$browserExit }
        artifacts = $iterationDirectory
    } | ConvertTo-Json -Compress
    Add-Content -Path $outcomeLog -Value $record
    "Iteration ${iteration}: $status" | Add-Content $summaryLog
    Write-Host "Iteration ${iteration}: $status" -ForegroundColor $(if ($status -eq 'passed') { 'Green' } else { 'Red' })

    if ($PauseSeconds -gt 0 -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds $PauseSeconds }
}

"Completed $(Get-Date -Format o)" | Add-Content $summaryLog
"Passed: $passed; Failed: $failed" | Add-Content $summaryLog
Write-Host "Endurance run complete. Passed: $passed; Failed: $failed" -ForegroundColor Cyan
Write-Host "Logs: $OutputDirectory" -ForegroundColor Cyan
if ($failed -gt 0) { exit 1 }
