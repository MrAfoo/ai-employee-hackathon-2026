#!/usr/bin/env pwsh
# Phase 5 - Real-time Metrics Dashboard

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI Employee Metrics Dashboard" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

function Show-Metrics {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  AI Employee Metrics Dashboard - $timestamp  ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # HPA Status
    Write-Host "📊 Horizontal Pod Autoscaler Status:" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    kubectl get hpa --all-namespaces --no-headers | ForEach-Object {
        Write-Host "  $_" -ForegroundColor White
    }
    Write-Host ""
    
    # Pod Status
    Write-Host "🚀 Pod Status:" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    kubectl get pods --all-namespaces --no-headers | Select-String "task-manager|workflow|reporting" | ForEach-Object {
        $line = $_.ToString()
        if ($line -match "Running") {
            Write-Host "  $_" -ForegroundColor Green
        } elseif ($line -match "Pending") {
            Write-Host "  $_" -ForegroundColor Yellow
        } else {
            Write-Host "  $_" -ForegroundColor Red
        }
    }
    Write-Host ""
    
    # Resource Usage
    Write-Host "💾 Resource Usage:" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    $metricsOutput = kubectl top pods --all-namespaces 2>&1
    if ($LASTEXITCODE -eq 0) {
        $metricsOutput | Select-String "task-manager|workflow|reporting" | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ⚠️  Metrics server not available" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Ingress Status
    Write-Host "🌐 Ingress Status:" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    kubectl get ingress --all-namespaces --no-headers | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Magenta
    }
    Write-Host ""
    
    Write-Host "Press Ctrl+C to exit | Refreshing every 5 seconds..." -ForegroundColor Gray
}

# Continuous monitoring
try {
    while ($true) {
        Show-Metrics
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host ""
    Write-Host "Dashboard stopped." -ForegroundColor Yellow
}
