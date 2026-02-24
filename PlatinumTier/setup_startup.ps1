# ── Platinum Tier: Local Agent Windows Startup Setup ─────────────────────────
# Registers local_agent.py as a Windows Task Scheduler job that runs
# automatically when you log in (i.e., when you open your laptop).
#
# Usage (run as Administrator):
#   .\setup_startup.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Platinum Tier: Local Agent Startup Setup ===" -ForegroundColor Cyan

# ── Paths ─────────────────────────────────────────────────────────────────────
$WorkDir    = Split-Path -Parent $PSScriptRoot
$PythonExe  = Join-Path $WorkDir ".venv\Scripts\python.exe"
$AgentScript = Join-Path $PSScriptRoot "local_agent.py"
$EnvFile    = Join-Path $PSScriptRoot ".env"
$LogFile    = Join-Path $PSScriptRoot "local_agent.log"

# Fallback to system python if venv not found
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        Write-Error "Python not found. Install Python 3.11+ first."
        exit 1
    }
    Write-Warning "Virtual environment not found. Using system Python: $PythonExe"
}

Write-Host "Python:  $PythonExe"
Write-Host "Script:  $AgentScript"
Write-Host "WorkDir: $WorkDir"

# ── Install dependencies ──────────────────────────────────────────────────────
Write-Host "`n[1/3] Installing dependencies..." -ForegroundColor Yellow
& $PythonExe -m pip install -r (Join-Path $PSScriptRoot "requirements.txt") -q
& $PythonExe -m playwright install chromium

# ── Create Task Scheduler entry ───────────────────────────────────────────────
Write-Host "`n[2/3] Registering Windows Task Scheduler job..." -ForegroundColor Yellow

$TaskName   = "AIEmployee-LocalAgent"
$Action     = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $AgentScript `
    -WorkingDirectory $PSScriptRoot

# Trigger: At logon (laptop wake/login)
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

# Also trigger on system unlock (simulate wake)
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register (or update existing)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  Removed existing task."
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $TriggerLogon `
    -Settings $Settings `
    -RunLevel Highest `
    -Description "AI Employee Local Agent – Platinum Tier. Handles WhatsApp, approvals, final send." | Out-Null

Write-Host "  ✅ Task '$TaskName' registered." -ForegroundColor Green

# ── Copy env file if missing ──────────────────────────────────────────────────
Write-Host "`n[3/3] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $PSScriptRoot ".env.example") $EnvFile
    Write-Warning "Created .env from template — fill in your credentials!"
} else {
    Write-Host "  .env exists." -ForegroundColor Green
}

# Set AGENT_MODE=local in .env
$envContent = Get-Content $EnvFile -Raw
$envContent = $envContent -replace "(?m)^AGENT_MODE=.*", "AGENT_MODE=local"
$envContent = $envContent -replace "(?m)^AGENT_NAME=.*", "AGENT_NAME=local"
Set-Content $EnvFile -Value $envContent -NoNewline

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "The Local Agent will now start automatically when you log in." -ForegroundColor Cyan
Write-Host ""
Write-Host "To start it now:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  Get-Content '$LogFile' -Wait"
Write-Host ""
Write-Host "To stop it:"
Write-Host "  Stop-ScheduledTask -TaskName '$TaskName'"
