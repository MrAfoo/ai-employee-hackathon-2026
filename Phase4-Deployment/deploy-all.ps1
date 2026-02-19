# ============================================================================
# AI Employee Hackathon 2026 - Phase 4 Deployment Script (PowerShell)
# ============================================================================
# This script deploys all three AI Employee services to Kubernetes
# Usage: .\deploy-all.ps1 [-Method helm|kubectl]
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
Write-ColorOutput Blue "  AI Employee Hackathon 2026 - Phase 4 Deployment"
Write-ColorOutput Blue "============================================================================"
Write-Output ""

# Check prerequisites
Write-ColorOutput Yellow "Checking prerequisites..."

if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: kubectl not found. Please install kubectl first."
    exit 1
}

if ($Method -eq "helm" -and !(Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: helm not found. Please install helm first."
    exit 1
}

Write-ColorOutput Green "✓ Prerequisites satisfied"
Write-Output ""

# Check cluster connection
Write-ColorOutput Yellow "Checking Kubernetes cluster connection..."
try {
    kubectl cluster-info | Out-Null
    Write-ColorOutput Green "✓ Connected to Kubernetes cluster"
    kubectl cluster-info | Select-Object -First 1
} catch {
    Write-ColorOutput Red "Error: Cannot connect to Kubernetes cluster"
    Write-Output "Please ensure your cluster is running (minikube start / kind create cluster)"
    exit 1
}
Write-Output ""

# Step 1: Create namespaces and resource quotas
Write-ColorOutput Blue "[1/4] Creating namespaces and resource quotas..."
kubectl apply -f Phase2-Code/k8s-namespaces/namespaces.yaml
kubectl apply -f Phase2-Code/k8s-namespaces/resource-quotas.yaml
Write-ColorOutput Green "✓ Namespaces created"
Write-Output ""

# Give namespaces a moment to be ready
Start-Sleep -Seconds 2

# Step 2: Deploy services based on method
if ($Method -eq "helm") {
    Write-ColorOutput Blue "[2/4] Deploying services using Helm..."
    
    # Task Manager
    Write-ColorOutput Yellow "  Deploying Task Manager..."
    helm upgrade --install task-manager ./Phase2-Code/task-manager/helm `
        --namespace task-manager `
        --create-namespace `
        --wait `
        --timeout 5m
    Write-ColorOutput Green "  ✓ Task Manager deployed"
    
    # Workflow Automation
    Write-ColorOutput Yellow "  Deploying Workflow Automation..."
    helm upgrade --install workflow-automation ./Phase2-Code/workflow-automation/helm `
        --namespace workflow `
        --create-namespace `
        --wait `
        --timeout 5m
    Write-ColorOutput Green "  ✓ Workflow Automation deployed"
    
    # Reporting Agent
    Write-ColorOutput Yellow "  Deploying Reporting Agent..."
    helm upgrade --install reporting-agent ./Phase2-Code/reporting-agent/helm `
        --namespace reporting `
        --create-namespace `
        --wait `
        --timeout 5m
    Write-ColorOutput Green "  ✓ Reporting Agent deployed"
    
} elseif ($Method -eq "kubectl") {
    Write-ColorOutput Blue "[2/4] Deploying services using kubectl..."
    
    # Task Manager
    Write-ColorOutput Yellow "  Deploying Task Manager..."
    kubectl apply -k Phase2-Code/task-manager/k8s --namespace task-manager
    Write-ColorOutput Green "  ✓ Task Manager deployed"
    
    # Workflow Automation
    Write-ColorOutput Yellow "  Deploying Workflow Automation..."
    kubectl apply -k Phase2-Code/workflow-automation/k8s --namespace workflow
    Write-ColorOutput Green "  ✓ Workflow Automation deployed"
    
    # Reporting Agent
    Write-ColorOutput Yellow "  Deploying Reporting Agent..."
    kubectl apply -k Phase2-Code/reporting-agent/k8s --namespace reporting
    Write-ColorOutput Green "  ✓ Reporting Agent deployed"
}

Write-Output ""

# Step 3: Wait for pods to be ready
Write-ColorOutput Blue "[3/4] Waiting for pods to be ready..."

Write-ColorOutput Yellow "  Waiting for Task Manager..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=task-manager -n task-manager --timeout=300s

Write-ColorOutput Yellow "  Waiting for Workflow Automation..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=workflow-automation -n workflow --timeout=300s

Write-ColorOutput Yellow "  Waiting for Reporting Agent..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=reporting-agent -n reporting --timeout=300s

Write-ColorOutput Green "✓ All pods are ready"
Write-Output ""

# Step 4: Display status
Write-ColorOutput Blue "[4/4] Deployment Status"
Write-Output ""

Write-ColorOutput Yellow "Task Manager (namespace: task-manager)"
kubectl get pods,svc,pvc -n task-manager
Write-Output ""

Write-ColorOutput Yellow "Workflow Automation (namespace: workflow)"
kubectl get pods,svc,pvc -n workflow
Write-Output ""

Write-ColorOutput Yellow "Reporting Agent (namespace: reporting)"
kubectl get pods,svc,pvc -n reporting
Write-Output ""

# Display access instructions
Write-ColorOutput Blue "============================================================================"
Write-ColorOutput Green "✓ Deployment Complete!"
Write-ColorOutput Blue "============================================================================"
Write-Output ""
Write-ColorOutput Yellow "Access the services:"
Write-Output ""
Write-Output "1. Task Manager:"
Write-Output "   kubectl port-forward -n task-manager svc/task-manager 8081:8080"
Write-Output "   curl http://localhost:8081/health"
Write-Output "   Open: http://localhost:8081/docs"
Write-Output ""
Write-Output "2. Workflow Automation:"
Write-Output "   kubectl port-forward -n workflow svc/workflow-automation 8082:8080"
Write-Output "   curl http://localhost:8082/health"
Write-Output "   Open: http://localhost:8082/docs"
Write-Output ""
Write-Output "3. Reporting Agent:"
Write-Output "   kubectl port-forward -n reporting svc/reporting-agent 8083:8080"
Write-Output "   curl http://localhost:8083/health"
Write-Output "   Open: http://localhost:8083/docs"
Write-Output ""
Write-ColorOutput Yellow "View logs:"
Write-Output "   kubectl logs -n task-manager -l app.kubernetes.io/name=task-manager"
Write-Output "   kubectl logs -n workflow -l app.kubernetes.io/name=workflow-automation"
Write-Output "   kubectl logs -n reporting -l app.kubernetes.io/name=reporting-agent"
Write-Output ""
Write-ColorOutput Yellow "Cleanup:"
Write-Output "   .\undeploy-all.ps1"
Write-Output ""
Write-ColorOutput Green "Happy AI Hacking! 🚀"
