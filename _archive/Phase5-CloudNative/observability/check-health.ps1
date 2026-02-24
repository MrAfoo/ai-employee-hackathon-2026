#!/usr/bin/env pwsh
# Phase 5 - Health Check Script for All AI Employees

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI Employee Health Check - Phase 5" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl not found. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# 1. Check HPA Status
Write-Host "=== Horizontal Pod Autoscaler Status ===" -ForegroundColor Yellow
kubectl get hpa --all-namespaces
Write-Host ""

# 2. Check Pod Status
Write-Host "=== Pod Status ===" -ForegroundColor Yellow
kubectl get pods --all-namespaces | Select-String "task-manager|workflow|reporting"
Write-Host ""

# 3. Check Services
Write-Host "=== Services ===" -ForegroundColor Yellow
kubectl get services --all-namespaces | Select-String "task-manager|workflow|reporting"
Write-Host ""

# 4. Check Ingress
Write-Host "=== Ingress Status ===" -ForegroundColor Yellow
kubectl get ingress --all-namespaces
Write-Host ""

# 5. Check Resource Usage (if metrics-server is available)
Write-Host "=== Resource Usage ===" -ForegroundColor Yellow
$metricsAvailable = kubectl top pods --all-namespaces 2>&1
if ($LASTEXITCODE -eq 0) {
    $metricsAvailable | Select-String "task-manager|workflow|reporting"
} else {
    Write-Host "Metrics server not available. Skipping resource usage check." -ForegroundColor Yellow
}
Write-Host ""

# 6. Check ConfigMaps and Secrets
Write-Host "=== ConfigMaps ===" -ForegroundColor Yellow
kubectl get configmaps --all-namespaces | Select-String "task-manager|workflow|reporting|app-config"
Write-Host ""

Write-Host "=== Secrets ===" -ForegroundColor Yellow
kubectl get secrets --all-namespaces | Select-String "task-manager|workflow|reporting|db-secret"
Write-Host ""

# 7. Test endpoints
Write-Host "=== Testing Endpoints ===" -ForegroundColor Yellow

$endpoints = @(
    @{Name="Task Manager"; URL="http://localhost/task"},
    @{Name="Workflow Automation"; URL="http://localhost/workflow"},
    @{Name="Reporting Agent"; URL="http://localhost/reporting"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✅ $($endpoint.Name): $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($endpoint.Name): Failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Health Check Complete" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
