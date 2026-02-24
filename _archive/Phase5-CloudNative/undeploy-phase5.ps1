#!/usr/bin/env pwsh
# Phase 5 - Cleanup Script
# Removes HPA, Ingress, ConfigMaps, and Secrets

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Phase 5 Cleanup Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Step 1: Delete Ingress
Write-Host "🌐 Deleting Ingress resources..." -ForegroundColor Yellow
kubectl delete -f Phase5-Code/ingress/ingress.yaml --ignore-not-found=true
Write-Host "✅ Ingress resources deleted" -ForegroundColor Green
Write-Host ""

# Step 2: Delete HPA
Write-Host "📊 Deleting Horizontal Pod Autoscalers..." -ForegroundColor Yellow
kubectl delete -f Phase5-Code/hpa/task-manager-hpa.yaml --ignore-not-found=true
kubectl delete -f Phase5-Code/hpa/workflow-automation-hpa.yaml --ignore-not-found=true
kubectl delete -f Phase5-Code/hpa/reporting-agent-hpa.yaml --ignore-not-found=true
Write-Host "✅ HPAs deleted" -ForegroundColor Green
Write-Host ""

# Step 3: Delete ConfigMaps
Write-Host "📝 Deleting ConfigMaps..." -ForegroundColor Yellow
kubectl delete -f Phase5-Code/config/configmaps.yaml --ignore-not-found=true
Write-Host "✅ ConfigMaps deleted" -ForegroundColor Green
Write-Host ""

# Step 4: Delete Secrets
Write-Host "🔐 Deleting Secrets..." -ForegroundColor Yellow
kubectl delete -f Phase5-Code/config/secrets.yaml --ignore-not-found=true
Write-Host "✅ Secrets deleted" -ForegroundColor Green
Write-Host ""

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Phase 5 Cleanup Complete! ✅" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
