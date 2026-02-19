#!/bin/bash

# ============================================================================
# AI Employee Hackathon 2026 - Phase 4 Cleanup Script
# ============================================================================
# This script removes all deployed AI Employee services from Kubernetes
# Usage: ./undeploy-all.sh [helm|kubectl]
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
echo -e "${BLUE}  AI Employee Hackathon 2026 - Phase 4 Cleanup${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Confirmation
echo -e "${YELLOW}This will remove all AI Employee services and their data.${NC}"
echo -e "${YELLOW}Are you sure you want to continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${BLUE}Cleanup cancelled.${NC}"
    exit 0
fi

echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found.${NC}"
    exit 1
fi

if [ "$DEPLOY_METHOD" == "helm" ] && ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo ""

# Step 1: Remove services
if [ "$DEPLOY_METHOD" == "helm" ]; then
    echo -e "${BLUE}[1/3] Uninstalling Helm releases...${NC}"
    
    echo -e "${YELLOW}  Uninstalling Task Manager...${NC}"
    helm uninstall task-manager -n task-manager 2>/dev/null || echo "  (already removed)"
    
    echo -e "${YELLOW}  Uninstalling Workflow Automation...${NC}"
    helm uninstall workflow-automation -n workflow 2>/dev/null || echo "  (already removed)"
    
    echo -e "${YELLOW}  Uninstalling Reporting Agent...${NC}"
    helm uninstall reporting-agent -n reporting 2>/dev/null || echo "  (already removed)"
    
    echo -e "${GREEN}✓ Helm releases removed${NC}"
    
elif [ "$DEPLOY_METHOD" == "kubectl" ]; then
    echo -e "${BLUE}[1/3] Removing Kubernetes resources...${NC}"
    
    echo -e "${YELLOW}  Removing Task Manager...${NC}"
    kubectl delete -k Phase2-Code/task-manager/k8s --namespace task-manager --ignore-not-found=true
    
    echo -e "${YELLOW}  Removing Workflow Automation...${NC}"
    kubectl delete -k Phase2-Code/workflow-automation/k8s --namespace workflow --ignore-not-found=true
    
    echo -e "${YELLOW}  Removing Reporting Agent...${NC}"
    kubectl delete -k Phase2-Code/reporting-agent/k8s --namespace reporting --ignore-not-found=true
    
    echo -e "${GREEN}✓ Kubernetes resources removed${NC}"
fi

echo ""

# Step 2: Remove PVCs (if any remain)
echo -e "${BLUE}[2/3] Cleaning up persistent volumes...${NC}"
kubectl delete pvc --all -n task-manager --ignore-not-found=true
kubectl delete pvc --all -n workflow --ignore-not-found=true
kubectl delete pvc --all -n reporting --ignore-not-found=true
echo -e "${GREEN}✓ Persistent volumes cleaned up${NC}"
echo ""

# Step 3: Remove namespaces
echo -e "${BLUE}[3/3] Removing namespaces...${NC}"
kubectl delete namespace task-manager --ignore-not-found=true
kubectl delete namespace workflow --ignore-not-found=true
kubectl delete namespace reporting --ignore-not-found=true
echo -e "${GREEN}✓ Namespaces removed${NC}"
echo ""

# Display final status
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✓ Cleanup Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Remaining namespaces:${NC}"
kubectl get namespaces | grep -E "NAME|task-manager|workflow|reporting" || echo "  All AI Employee namespaces removed"
echo ""
echo -e "${YELLOW}Remaining PVs:${NC}"
kubectl get pv | grep -E "NAME|task-manager|workflow|reporting" || echo "  All AI Employee persistent volumes removed"
echo ""
echo -e "${GREEN}You can redeploy anytime with: ./deploy-all.sh${NC}"
