# ============================================
# AI Employee - Port Forward Script
# ============================================
# Starts port-forwards for all services and
# keeps running until you press Ctrl+C
# ============================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   AI Employee - Port Forward Manager    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing port-forwards first
Write-Host "Stopping any existing port-forwards..." -ForegroundColor Yellow
Get-Process kubectl -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   Done." -ForegroundColor Gray
Write-Host ""

# Start all port-forwards using Start-Process
Write-Host "Starting port-forwards..." -ForegroundColor Green
Write-Host ""

# Landing Page - 8080
Write-Host "   Landing Page        -> http://localhost:8080" -ForegroundColor White
$proc0 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n default svc/landing-page 8080:8080" `
    -PassThru -WindowStyle Hidden

# Task Manager - 8081
Write-Host "   Task Manager        -> http://localhost:8081" -ForegroundColor White
$proc1 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n default svc/task-manager 8081:8080" `
    -PassThru -WindowStyle Hidden

# Workflow Automation - 8082 (port-forward directly to pod for reliability)
Write-Host "   Workflow Automation -> http://localhost:8082" -ForegroundColor White
$wfPod = kubectl get pod -n default -l app.kubernetes.io/name=workflow-automation -o jsonpath='{.items[0].metadata.name}'
$proc2 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n default pod/$wfPod 8082:8080" `
    -PassThru -WindowStyle Hidden

# Reporting Agent - 8083
Write-Host "   Reporting Agent     -> http://localhost:8083" -ForegroundColor White
$proc3 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n default svc/reporting-agent 8083:8080" `
    -PassThru -WindowStyle Hidden

# Prometheus - 9090
Write-Host "   Prometheus          -> http://localhost:9090" -ForegroundColor White
$proc4 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n monitoring svc/prometheus-server 9090:80" `
    -PassThru -WindowStyle Hidden

# Grafana - 3000
Write-Host "   Grafana             -> http://localhost:3000  (admin/hackathon123)" -ForegroundColor White
$proc5 = Start-Process -FilePath "kubectl" `
    -ArgumentList "port-forward -n monitoring svc/grafana 3000:80" `
    -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 5
Write-Host ""

# Test each service
Write-Host "Testing services..." -ForegroundColor Cyan
Write-Host ""

$services = @(
    @{Name="Task Manager    (8081)"; Url="http://localhost:8081/health"; Proc=$proc1},
    @{Name="Workflow Auto   (8082)"; Url="http://localhost:8082/health"; Proc=$proc2},
    @{Name="Reporting Agent (8083)"; Url="http://localhost:8083/health"; Proc=$proc3},
    @{Name="Prometheus      (9090)"; Url="http://localhost:9090/-/healthy"; Proc=$proc4},
    @{Name="Grafana         (3000)"; Url="http://localhost:3000/api/health"; Proc=$proc5}
)

foreach ($svc in $services) {
    try {
        $resp = Invoke-RestMethod -Uri $svc.Url -TimeoutSec 5 -ErrorAction Stop
        Write-Host "   OK  $($svc.Name)" -ForegroundColor Green
    } catch {
        Write-Host "   --  $($svc.Name) (starting up...)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   SERVICE URLS                          " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  AI Services:" -ForegroundColor Yellow
Write-Host "    Task Manager API:     http://localhost:8081" -ForegroundColor White
Write-Host "    Task Manager Docs:    http://localhost:8081/docs" -ForegroundColor White
Write-Host "    Task Demo Tasks:      http://localhost:8081/demo/tasks" -ForegroundColor White
Write-Host "    Task Demo Summary:    http://localhost:8081/demo/summary" -ForegroundColor White
Write-Host ""
Write-Host "    Workflow API:         http://localhost:8082" -ForegroundColor White
Write-Host "    Workflow Docs:        http://localhost:8082/docs" -ForegroundColor White
Write-Host "    Workflow Demo:        http://localhost:8082/demo/workflows" -ForegroundColor White
Write-Host "    Workflow Logs Demo:   http://localhost:8082/demo/logs" -ForegroundColor White
Write-Host ""
Write-Host "    Reporting API:        http://localhost:8083" -ForegroundColor White
Write-Host "    Reporting Docs:       http://localhost:8083/docs" -ForegroundColor White
Write-Host "    Daily Report:         http://localhost:8083/demo/daily" -ForegroundColor White
Write-Host "    Weekly Report:        http://localhost:8083/demo/weekly" -ForegroundColor White
Write-Host "    Alerts:               http://localhost:8083/demo/alerts" -ForegroundColor White
Write-Host "    All Reports:          http://localhost:8083/demo/reports" -ForegroundColor White
Write-Host "    Daily Markdown:       http://localhost:8083/demo/daily/markdown" -ForegroundColor White
Write-Host ""
Write-Host "  Observability:" -ForegroundColor Yellow
Write-Host "    Prometheus:           http://localhost:9090" -ForegroundColor White
Write-Host "    Grafana:              http://localhost:3000" -ForegroundColor White
Write-Host "    Grafana Login:        admin / hackathon123" -ForegroundColor White
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop all port-forwards " -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Define services for auto-restart monitoring
$portForwards = @(
    @{Name="landing-page";        Namespace="default";    Port="8080:8080"; Proc=[ref]$proc0},
    @{Name="task-manager";        Namespace="default";    Port="8081:8080"; Proc=[ref]$proc1},
    @{Name="workflow-automation"; Namespace="default";    Port="8082:8080"; Proc=[ref]$proc2},
    @{Name="reporting-agent";     Namespace="default";    Port="8083:8080"; Proc=[ref]$proc3},
    @{Name="prometheus-server";   Namespace="monitoring"; Port="9090:80";   Proc=[ref]$proc4},
    @{Name="grafana";             Namespace="monitoring"; Port="3000:80";   Proc=[ref]$proc5}
)

# Keep running and auto-restart crashed port-forwards
try {
    while ($true) {
        Start-Sleep -Seconds 15
        foreach ($pf in $portForwards) {
            if ($pf.Proc.Value.HasExited) {
                Write-Host "$(Get-Date -Format 'HH:mm:ss') - $($pf.Name) port-forward stopped, restarting..." -ForegroundColor Yellow
                $newProc = Start-Process -FilePath "kubectl" `
                    -ArgumentList "port-forward -n $($pf.Namespace) svc/$($pf.Name) $($pf.Port)" `
                    -PassThru -WindowStyle Hidden
                $pf.Proc.Value = $newProc
                Write-Host "   Restarted PID: $($newProc.Id)" -ForegroundColor Green
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "Stopping all port-forwards..." -ForegroundColor Yellow
    Get-Process kubectl -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "All port-forwards stopped. Goodbye!" -ForegroundColor Green
    Write-Host ""
}
