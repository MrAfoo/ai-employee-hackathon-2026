#!/usr/bin/env pwsh
# Phase 5 - Deployment Script
# Deploys HPA, Ingress, ConfigMaps, and Secrets

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipNginx
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Phase 5 Deployment Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ kubectl not found. Please install kubectl first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ kubectl found" -ForegroundColor Green
Write-Host ""

# Step 0: Create Namespaces
Write-Host "📁 Creating Namespaces..." -ForegroundColor Yellow
$namespaces = @("task-manager", "workflow", "reporting")
foreach ($ns in $namespaces) {
    $exists = kubectl get namespace $ns 2>&1
    if ($LASTEXITCODE -ne 0) {
        kubectl create namespace $ns
        Write-Host "  ✅ Namespace '$ns' created" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Namespace '$ns' already exists" -ForegroundColor Yellow
    }
}
Write-Host ""

# Step 1: Install NGINX Ingress Controller
if (-not $SkipNginx) {
    Write-Host "📦 Installing NGINX Ingress Controller..." -ForegroundColor Yellow
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    
    Write-Host "⏳ Waiting for NGINX Ingress Controller to be ready..." -ForegroundColor Yellow
    kubectl wait --namespace ingress-nginx `
        --for=condition=ready pod `
        --selector=app.kubernetes.io/component=controller `
        --timeout=120s
    Write-Host "✅ NGINX Ingress Controller installed" -ForegroundColor Green
} else {
    Write-Host "⏭️  Skipping NGINX installation" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Apply ConfigMaps
Write-Host "📝 Creating ConfigMaps..." -ForegroundColor Yellow
kubectl apply -f "$PSScriptRoot/config/configmaps.yaml"
Write-Host "✅ ConfigMaps created" -ForegroundColor Green
Write-Host ""

# Step 3: Apply Secrets
Write-Host "🔐 Creating Secrets..." -ForegroundColor Yellow
kubectl apply -f "$PSScriptRoot/config/secrets.yaml"
Write-Host "✅ Secrets created" -ForegroundColor Green
Write-Host ""

# Step 4: Apply HPA
Write-Host "📊 Creating Horizontal Pod Autoscalers..." -ForegroundColor Yellow
kubectl apply -f "$PSScriptRoot/hpa/task-manager-hpa.yaml"
kubectl apply -f "$PSScriptRoot/hpa/workflow-automation-hpa.yaml"
kubectl apply -f "$PSScriptRoot/hpa/reporting-agent-hpa.yaml"
Write-Host "✅ HPAs created" -ForegroundColor Green
Write-Host ""

# Step 5: Apply Ingress
Write-Host "🌐 Creating Ingress resources..." -ForegroundColor Yellow
kubectl apply -f "$PSScriptRoot/ingress/ingress.yaml"
Write-Host "✅ Ingress resources created" -ForegroundColor Green
Write-Host ""

# Step 6: Verify deployment
Write-Host "🔍 Verifying deployment..." -ForegroundColor Yellow
Write-Host ""

Write-Host "HPA Status:" -ForegroundColor Cyan
kubectl get hpa --all-namespaces
Write-Host ""

Write-Host "Ingress Status:" -ForegroundColor Cyan
kubectl get ingress --all-namespaces
Write-Host ""

Write-Host "ConfigMaps:" -ForegroundColor Cyan
kubectl get configmaps --all-namespaces | Select-String "app-config|task-manager|workflow|reporting"
Write-Host ""

Write-Host "Secrets:" -ForegroundColor Cyan
kubectl get secrets --all-namespaces | Select-String "db-secret|task-manager|workflow|reporting"
Write-Host ""

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Phase 5 Deployment Complete! ✅" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Check health: .\observability\check-health.ps1" -ForegroundColor White
Write-Host "  2. View logs: .\observability\view-logs.ps1" -ForegroundColor White
Write-Host "  3. Monitor metrics: .\observability\metrics-dashboard.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Access endpoints:" -ForegroundColor Yellow
Write-Host "  - Task Manager: http://localhost/task" -ForegroundColor White
Write-Host "  - Workflow Automation: http://localhost/workflow" -ForegroundColor White
Write-Host "  - Reporting Agent: http://localhost/reporting" -ForegroundColor White
