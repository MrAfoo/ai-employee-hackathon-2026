#!/usr/bin/env pwsh
# Phase 5 - Ingress Testing Script
# Test all ingress endpoints

Write-Host "=== Phase 5: Testing Ingress Endpoints ===" -ForegroundColor Cyan
Write-Host ""

$endpoints = @(
    @{Name="Task Manager"; URL="http://localhost/task"},
    @{Name="Workflow Automation"; URL="http://localhost/workflow"},
    @{Name="Reporting Agent"; URL="http://localhost/reporting"}
)

Write-Host "Testing ingress endpoints..." -ForegroundColor Yellow
Write-Host ""

foreach ($endpoint in $endpoints) {
    Write-Host "Testing $($endpoint.Name)..." -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -UseBasicParsing -TimeoutSec 5
        Write-Host "  ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== Ingress Configuration ===" -ForegroundColor Cyan
kubectl get ingress --all-namespaces

Write-Host ""
Write-Host "=== NGINX Ingress Controller Status ===" -ForegroundColor Cyan
kubectl get pods -n ingress-nginx
