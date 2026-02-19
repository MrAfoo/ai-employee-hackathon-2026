# ============================================================================
# AI Employee Hackathon 2026 - Phase 4 Cleanup Script (PowerShell)
# ============================================================================
# This script removes all deployed AI Employee services from Kubernetes
# Usage: .\undeploy-all.ps1 [-Method helm|kubectl]
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('helm', 'kubectl')]
    [string]$Method = 'helm'
)

$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue "============================================================================"
Write-ColorOutput Blue "  AI Employee Hackathon 2026 - Phase 4 Cleanup"
Write-ColorOutput Blue "============================================================================"
Write-Output ""

# Confirmation
Write-ColorOutput Yellow "This will remove all AI Employee services and their data."
$Confirm = Read-Host "Are you sure you want to continue? (yes/no)"

if ($Confirm -ne "yes") {
    Write-ColorOutput Blue "Cleanup cancelled."
    exit 0
}

Write-Output ""

# Check prerequisites
Write-ColorOutput Yellow "Checking prerequisites..."

if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: kubectl not found."
    exit 1
}

if ($Method -eq "helm" -and !(Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: helm not found."
    exit 1
}

Write-ColorOutput Green "✓ Prerequisites satisfied"
Write-Output ""

# Step 1: Remove services
if ($Method -eq "helm") {
    Write-ColorOutput Blue "[1/3] Uninstalling Helm releases..."
    
    Write-ColorOutput Yellow "  Uninstalling Task Manager..."
    try { helm uninstall task-manager -n task-manager } catch { Write-Output "  (already removed)" }
    
    Write-ColorOutput Yellow "  Uninstalling Workflow Automation..."
    try { helm uninstall workflow-automation -n workflow } catch { Write-Output "  (already removed)" }
    
    Write-ColorOutput Yellow "  Uninstalling Reporting Agent..."
    try { helm uninstall reporting-agent -n reporting } catch { Write-Output "  (already removed)" }
    
    Write-ColorOutput Green "✓ Helm releases removed"
    
} elseif ($Method -eq "kubectl") {
    Write-ColorOutput Blue "[1/3] Removing Kubernetes resources..."
    
    Write-ColorOutput Yellow "  Removing Task Manager..."
    kubectl delete -k Phase2-Code/task-manager/k8s --namespace task-manager --ignore-not-found=true
    
    Write-ColorOutput Yellow "  Removing Workflow Automation..."
    kubectl delete -k Phase2-Code/workflow-automation/k8s --namespace workflow --ignore-not-found=true
    
    Write-ColorOutput Yellow "  Removing Reporting Agent..."
    kubectl delete -k Phase2-Code/reporting-agent/k8s --namespace reporting --ignore-not-found=true
    
    Write-ColorOutput Green "✓ Kubernetes resources removed"
}

Write-Output ""

# Step 2: Remove PVCs
Write-ColorOutput Blue "[2/3] Cleaning up persistent volumes..."
kubectl delete pvc --all -n task-manager --ignore-not-found=true
kubectl delete pvc --all -n workflow --ignore-not-found=true
kubectl delete pvc --all -n reporting --ignore-not-found=true
Write-ColorOutput Green "✓ Persistent volumes cleaned up"
Write-Output ""

# Step 3: Remove namespaces
Write-ColorOutput Blue "[3/3] Removing namespaces..."
kubectl delete namespace task-manager --ignore-not-found=true
kubectl delete namespace workflow --ignore-not-found=true
kubectl delete namespace reporting --ignore-not-found=true
Write-ColorOutput Green "✓ Namespaces removed"
Write-Output ""

# Display final status
Write-ColorOutput Blue "============================================================================"
Write-ColorOutput Green "✓ Cleanup Complete!"
Write-ColorOutput Blue "============================================================================"
Write-Output ""
Write-ColorOutput Yellow "Remaining namespaces:"
kubectl get namespaces | Select-String -Pattern "task-manager|workflow|reporting"
Write-Output ""
Write-ColorOutput Green "You can redeploy anytime with: .\deploy-all.ps1"
