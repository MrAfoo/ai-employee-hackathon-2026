# start_all.ps1 – One-click AI Employee startup for Windows
# Launches all components in separate terminal windows:
#   1. Orchestrator (Bronze Tier – master controller)
#   2. HITL Orchestrator (watches /Approved + /Rejected)
#   3. Silver Tier MCP Email Server
#   4. Watchdog Monitor (auto-restarts crashed processes)
#
# Usage:
#   Right-click → Run with PowerShell
#   OR: powershell -ExecutionPolicy Bypass -File start_all.ps1

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BRONZE = Join-Path $ROOT "BronzeTier"
$SILVER = Join-Path $ROOT "SilverTier"
$VAULT  = Join-Path $ROOT "Vault"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Employee – Starting All Systems" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ──────────────────────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
$pyver = python --version 2>&1
Write-Host "✅ Python: $pyver" -ForegroundColor Green

# ── Check .env files ──────────────────────────────────────────────────────────
$bronzeEnv = Join-Path $BRONZE ".env"
$silverEnv = Join-Path $SILVER ".env"

if (-not (Test-Path $bronzeEnv)) {
    Write-Host "❌ BronzeTier/.env not found. Copy .env.example and fill in credentials." -ForegroundColor Red
    exit 1
}
Write-Host "✅ BronzeTier/.env found" -ForegroundColor Green

if (-not (Test-Path $silverEnv)) {
    Write-Host "⚠️  SilverTier/.env not found — MCP email server will use BronzeTier/.env" -ForegroundColor Yellow
    $silverEnv = $bronzeEnv
}

# ── Ensure Vault folders exist ────────────────────────────────────────────────
$folders = @("Needs_Action","Inbox","Done","Pending_Approval","Approved","Rejected","Accounting","Drop","Finance_Drop","Quarantine")
foreach ($f in $folders) {
    $p = Join-Path $VAULT $f
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p | Out-Null
        Write-Host "📁 Created: Vault/$f" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Starting components..." -ForegroundColor Cyan
Write-Host ""

# ── 1. Watchdog Monitor (keeps Orchestrator alive) ────────────────────────────
Write-Host "🐕 [1/4] Starting Watchdog Monitor..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee – Watchdog'; python watchdog_monitor.py"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# ── 2. HITL Orchestrator (watches Approved/Rejected) ─────────────────────────
Write-Host "🤝 [2/4] Starting HITL Orchestrator..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee – HITL Approvals'; python hitl_orchestrator.py"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# ── 3. Silver Tier MCP Email Server ───────────────────────────────────────────
$mcpServer = Join-Path $SILVER "mcp_servers\email_mcp_server.py"
if (Test-Path $mcpServer) {
    Write-Host "📧 [3/4] Starting MCP Email Server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$SILVER'; `$host.UI.RawUI.WindowTitle = 'AI Employee – MCP Email Server'; python mcp_servers/email_mcp_server.py"
    ) -WindowStyle Normal
    Start-Sleep -Seconds 2
} else {
    Write-Host "⚠️  [3/4] MCP Email Server not found — skipping" -ForegroundColor DarkGray
}

# ── 4. Main Orchestrator ───────────────────────────────────────────────────────
Write-Host "🤖 [4/4] Starting Main Orchestrator..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee – Orchestrator'; python Orchestrator.py"
) -WindowStyle Normal

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ✅ All systems launched!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Vault path : $VAULT" -ForegroundColor White
Write-Host ""
Write-Host "  How to use:" -ForegroundColor White
Write-Host "    Drop .md files into  : Vault\Needs_Action\" -ForegroundColor Gray
Write-Host "    Drop CSV files into  : Vault\Finance_Drop\" -ForegroundColor Gray
Write-Host "    Drop any file into   : Vault\Drop\" -ForegroundColor Gray
Write-Host "    Approve actions in   : Vault\Pending_Approval\ → move to Vault\Approved\" -ForegroundColor Gray
Write-Host "    View completed items : Vault\Done\" -ForegroundColor Gray
Write-Host ""
Write-Host "  To stop all: Close the terminal windows or press Ctrl+C in each." -ForegroundColor DarkGray
Write-Host ""

# ── Optional: Register as startup task ────────────────────────────────────────
$registerStartup = Read-Host "Register as Windows startup task? (runs automatically on login) [y/N]"
if ($registerStartup -eq 'y' -or $registerStartup -eq 'Y') {
    $taskName = "AIEmployee-StartAll"
    $taskPath = $MyInvocation.MyCommand.Path
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$taskPath`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-Host "✅ Startup task registered: '$taskName'" -ForegroundColor Green
    Write-Host "   AI Employee will start automatically on Windows login." -ForegroundColor Gray
    Write-Host "   To remove: schtasks /delete /tn AIEmployee-StartAll /f" -ForegroundColor DarkGray
}
