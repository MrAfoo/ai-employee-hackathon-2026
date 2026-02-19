#!/usr/bin/env pwsh
# Phase 5 - Install NGINX Ingress Controller
# Works with Kind, Minikube, and standard Kubernetes

param(
    [Parameter()]
    [ValidateSet("kind", "minikube", "default")]
    [string]$Platform = "kind"
)

Write-Host "=== Phase 5: Installing NGINX Ingress Controller ===" -ForegroundColor Cyan
Write-Host ""

switch ($Platform) {
    "kind" {
        Write-Host "Installing NGINX Ingress for Kind..." -ForegroundColor Yellow
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    }
    "minikube" {
        Write-Host "Enabling NGINX Ingress for Minikube..." -ForegroundColor Yellow
        minikube addons enable ingress
    }
    "default" {
        Write-Host "Installing NGINX Ingress (Cloud Provider)..." -ForegroundColor Yellow
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
    }
}

Write-Host ""
Write-Host "Waiting for NGINX Ingress Controller to be ready..." -ForegroundColor Yellow
kubectl wait --namespace ingress-nginx `
  --for=condition=ready pod `
  --selector=app.kubernetes.io/component=controller `
  --timeout=90s

Write-Host ""
Write-Host "✅ NGINX Ingress Controller installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Ingress Controller Pods:" -ForegroundColor Cyan
kubectl get pods -n ingress-nginx
