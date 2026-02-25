# ============================================================
#  AI Employee - Start All Services
#  Run: powershell -ExecutionPolicy Bypass -File start_all.ps1
# ============================================================

$ROOT    = $PSScriptRoot
$BRONZE  = Join-Path $ROOT "BronzeTier"
$SILVER  = Join-Path $ROOT "SilverTier"
$VAULT   = Join-Path $ROOT "Vault"

# ── Ensure Vault folders exist ───────────────────────────────
$folders = @(
    "Needs_Action","Inbox","Done",
    "Pending_Approval","Approved","Rejected",
    "Accounting","Finance_Drop","Drop","Quarantine"
)
foreach ($f in $folders) {
    $p = Join-Path $VAULT $f
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Employee - Launching All Services"          -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Set PYTHONPATH so all imports resolve correctly ───────────
$env:PYTHONPATH = "$BRONZE;$ROOT"

# ── Window 1: Watchdog Monitor ───────────────────────────────
Write-Host "  [1/4] Starting Watchdog Monitor..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$env:PYTHONPATH='$BRONZE;$ROOT'; cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee - Watchdog'; python watchdog_monitor.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ── Window 2: HITL Approval Orchestrator ─────────────────────
Write-Host "  [2/4] Starting HITL Approval Monitor..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$env:PYTHONPATH='$BRONZE;$ROOT'; cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee - HITL Approvals'; python hitl_orchestrator.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ── Window 3: Email MCP Server ───────────────────────────────
Write-Host "  [3/4] Starting Email MCP Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$env:PYTHONPATH='$BRONZE;$ROOT'; cd '$ROOT'; `$host.UI.RawUI.WindowTitle = 'AI Employee - Email MCP'; python SilverTier/mcp_servers/email_mcp_server.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ── Window 4: Main Orchestrator ──────────────────────────────
Write-Host "  [4/4] Starting Main Orchestrator..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$env:PYTHONPATH='$BRONZE;$ROOT'; cd '$BRONZE'; `$host.UI.RawUI.WindowTitle = 'AI Employee - Orchestrator'; python Orchestrator.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  All systems launched!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Vault path  : $VAULT"                           -ForegroundColor White
Write-Host ""
Write-Host "  How to use:"                                    -ForegroundColor White
Write-Host "    Drop .md files into  : Vault\Needs_Action\"  -ForegroundColor Gray
Write-Host "    Drop CSV files into  : Vault\Finance_Drop\"  -ForegroundColor Gray
Write-Host "    Approve actions in   : Vault\Pending_Approval\" -ForegroundColor Gray
Write-Host "    Move approved to     : Vault\Approved\"       -ForegroundColor Gray
Write-Host "    View results in      : Vault\Done\"           -ForegroundColor Gray
Write-Host "    Live dashboard       : Vault\Dashboard.md"    -ForegroundColor Gray
Write-Host "    Current plan         : Vault\Plan.md"         -ForegroundColor Gray
Write-Host ""

# ── Optional: Register as Windows startup task ───────────────
$answer = Read-Host "Register as Windows startup task? (runs on every login) [y/N]"
if ($answer -match "^[yY]") {
    $action  = "powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ROOT\start_all.ps1`""
    $trigger = "ONLOGON"
    schtasks /create /tn "AIEmployee-StartAll" /tr $action /sc $trigger /rl HIGHEST /f 2>&1 | Out-Null
    Write-Host ""
    Write-Host "  Registered! AI Employee will start on every Windows login." -ForegroundColor Green
    Write-Host "  To remove: schtasks /delete /tn AIEmployee-StartAll /f"     -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "  Skipped startup registration." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
