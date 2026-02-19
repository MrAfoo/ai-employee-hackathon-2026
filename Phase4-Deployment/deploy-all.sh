#!/bin/bash

# ============================================================================
# AI Employee Hackathon 2026 - Phase 4 Deployment Script
# ============================================================================
# This script deploys all three AI Employee services to Kubernetes
# Usage: ./deploy-all.sh [helm|kubectl]
# ============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Deployment method (default: helm)
DEPLOY_METHOD=${1:-helm}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  AI Employee Hackathon 2026 - Phase 4 Deployment${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

if [ "$DEPLOY_METHOD" == "helm" ] && ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm not found. Please install helm first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo ""

# Check cluster connection
echo -e "${YELLOW}Checking Kubernetes cluster connection...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure your cluster is running (minikube start / kind create cluster)"
    exit 1
fi

echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
kubectl cluster-info | head -n 1
echo ""

# Step 1: Create namespaces and resource quotas
echo -e "${BLUE}[1/4] Creating namespaces and resource quotas...${NC}"
kubectl apply -f Phase2-Code/k8s-namespaces/namespaces.yaml
kubectl apply -f Phase2-Code/k8s-namespaces/resource-quotas.yaml
echo -e "${GREEN}✓ Namespaces created${NC}"
echo ""

# Give namespaces a moment to be ready
sleep 2

# Step 2: Deploy services based on method
if [ "$DEPLOY_METHOD" == "helm" ]; then
    echo -e "${BLUE}[2/4] Deploying services using Helm...${NC}"
    
    # Task Manager
    echo -e "${YELLOW}  Deploying Task Manager...${NC}"
    helm upgrade --install task-manager ./Phase2-Code/task-manager/helm \
        --namespace task-manager \
        --create-namespace \
        --wait \
        --timeout 5m
    echo -e "${GREEN}  ✓ Task Manager deployed${NC}"
    
    # Workflow Automation
    echo -e "${YELLOW}  Deploying Workflow Automation...${NC}"
    helm upgrade --install workflow-automation ./Phase2-Code/workflow-automation/helm \
        --namespace workflow \
        --create-namespace \
        --wait \
        --timeout 5m
    echo -e "${GREEN}  ✓ Workflow Automation deployed${NC}"
    
    # Reporting Agent
    echo -e "${YELLOW}  Deploying Reporting Agent...${NC}"
    helm upgrade --install reporting-agent ./Phase2-Code/reporting-agent/helm \
        --namespace reporting \
        --create-namespace \
        --wait \
        --timeout 5m
    echo -e "${GREEN}  ✓ Reporting Agent deployed${NC}"
    
elif [ "$DEPLOY_METHOD" == "kubectl" ]; then
    echo -e "${BLUE}[2/4] Deploying services using kubectl...${NC}"
    
    # Task Manager
    echo -e "${YELLOW}  Deploying Task Manager...${NC}"
    kubectl apply -k Phase2-Code/task-manager/k8s --namespace task-manager
    echo -e "${GREEN}  ✓ Task Manager deployed${NC}"
    
    # Workflow Automation
    echo -e "${YELLOW}  Deploying Workflow Automation...${NC}"
    kubectl apply -k Phase2-Code/workflow-automation/k8s --namespace workflow
    echo -e "${GREEN}  ✓ Workflow Automation deployed${NC}"
    
    # Reporting Agent
    echo -e "${YELLOW}  Deploying Reporting Agent...${NC}"
    kubectl apply -k Phase2-Code/reporting-agent/k8s --namespace reporting
    echo -e "${GREEN}  ✓ Reporting Agent deployed${NC}"
else
    echo -e "${RED}Error: Invalid deployment method. Use 'helm' or 'kubectl'${NC}"
    exit 1
fi

echo ""

# Step 3: Wait for pods to be ready
echo -e "${BLUE}[3/4] Waiting for pods to be ready...${NC}"

echo -e "${YELLOW}  Waiting for Task Manager...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=task-manager -n task-manager --timeout=300s || true

echo -e "${YELLOW}  Waiting for Workflow Automation...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=workflow-automation -n workflow --timeout=300s || true

echo -e "${YELLOW}  Waiting for Reporting Agent...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=reporting-agent -n reporting --timeout=300s || true

echo -e "${GREEN}✓ All pods are ready${NC}"
echo ""

# Step 4: Display status
echo -e "${BLUE}[4/4] Deployment Status${NC}"
echo ""

echo -e "${YELLOW}Task Manager (namespace: task-manager)${NC}"
kubectl get pods,svc,pvc -n task-manager
echo ""

echo -e "${YELLOW}Workflow Automation (namespace: workflow)${NC}"
kubectl get pods,svc,pvc -n workflow
echo ""

echo -e "${YELLOW}Reporting Agent (namespace: reporting)${NC}"
kubectl get pods,svc,pvc -n reporting
echo ""

# Display access instructions
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Access the services:${NC}"
echo ""
echo "1. Task Manager:"
echo "   kubectl port-forward -n task-manager svc/task-manager 8081:8080"
echo "   curl http://localhost:8081/health"
echo "   Open: http://localhost:8081/docs"
echo ""
echo "2. Workflow Automation:"
echo "   kubectl port-forward -n workflow svc/workflow-automation 8082:8080"
echo "   curl http://localhost:8082/health"
echo "   Open: http://localhost:8082/docs"
echo ""
echo "3. Reporting Agent:"
echo "   kubectl port-forward -n reporting svc/reporting-agent 8083:8080"
echo "   curl http://localhost:8083/health"
echo "   Open: http://localhost:8083/docs"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "   kubectl logs -n task-manager -l app.kubernetes.io/name=task-manager"
echo "   kubectl logs -n workflow -l app.kubernetes.io/name=workflow-automation"
echo "   kubectl logs -n reporting -l app.kubernetes.io/name=reporting-agent"
echo ""
echo -e "${YELLOW}Cleanup:${NC}"
echo "   ./undeploy-all.sh"
echo ""
echo -e "${GREEN}Happy AI Hacking! 🚀${NC}"
