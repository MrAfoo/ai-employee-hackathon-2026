# Reporting Agent AI Employee - Deployment Guide

Comprehensive deployment guide for production and development environments.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Configuration](#configuration)
5. [Integration Setup](#integration-setup)
6. [Monitoring & Observability](#monitoring--observability)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Reporting Agent                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Data         │    │ Report       │                   │
│  │ Collector    │───▶│ Generator    │                   │
│  └──────────────┘    └──────────────┘                   │
│         │                    │                           │
│         ▼                    ▼                           │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Task Manager │    │ AI Analyzer  │                   │
│  │ Integration  │    │ (Ollama LLM) │                   │
│  └──────────────┘    └──────────────┘                   │
│         │                    │                           │
│         ▼                    ▼                           │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Workflow     │    │ Export       │                   │
│  │ Integration  │    │ (MD/JSON)    │                   │
│  └──────────────┘    └──────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
  Persistent Storage      Report Output
  (PVC: 7Gi total)       (Markdown/JSON)
```

---

## Prerequisites

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 10GB
- **OS**: Linux, macOS, Windows (with WSL2)

### Software Requirements

#### For Docker Deployment
- Docker 24.0+
- Docker Compose 2.20+

#### For Kubernetes Deployment
- Kubernetes 1.25+
- Helm 3.12+
- kubectl configured

#### Local Kubernetes Options
- Kind 0.20+
- Minikube 1.31+
- K3s 1.27+

---

## Deployment Options

### Option 1: Docker Compose (Development)

#### Basic Deployment

```bash
cd Phase2-Code/reporting-agent

# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f reporting-agent

# Check health
curl http://localhost:8080/health
```

#### With Full AI Employee Stack

```bash
# Deploy all three AI Employees
cd Phase2-Code

# Start Task Manager
cd task-manager && docker-compose up -d && cd ..

# Start Workflow Automation
cd workflow-automation && docker-compose up -d && cd ..

# Start Reporting Agent
cd reporting-agent && docker-compose up -d && cd ..

# Verify all services
docker ps | grep -E '(task-manager|workflow-automation|reporting-agent)'
```

---

### Option 2: Kubernetes with Helm (Production)

#### Install Single Instance

```bash
cd Phase2-Code/reporting-agent

# Create namespace
kubectl create namespace ai-employees

# Install with Helm
helm install reporting-agent ./helm \
  --namespace ai-employees \
  --set persistence.enabled=true \
  --set replicaCount=1

# Check deployment
kubectl get all -n ai-employees -l app.kubernetes.io/name=reporting-agent

# Wait for ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=reporting-agent \
  -n ai-employees \
  --timeout=300s
```

#### Production Configuration

Create `values-production.yaml`:

```yaml
replicaCount: 2

image:
  tag: "1.0.0"
  pullPolicy: Always

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

persistence:
  enabled: true
  reports:
    size: 10Gi
    storageClass: fast-ssd
  data:
    size: 5Gi
    storageClass: fast-ssd

reporting:
  dailySchedule: "0 9 * * *"    # 9 AM daily
  weeklySchedule: "0 9 * * 1"   # 9 AM Monday
  
integration:
  taskManager:
    enabled: true
    url: "http://task-manager:8080"
  workflowAutomation:
    enabled: true
    url: "http://workflow-automation:8080"

ollama:
  enabled: true
  model: llama2
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
```

Deploy:

```bash
helm install reporting-agent ./helm \
  --namespace ai-employees \
  --values values-production.yaml
```

#### Deploy Full AI Employee Stack

```bash
# Create namespace
kubectl create namespace ai-employees

# Install Task Manager
helm install task-manager ../task-manager/helm \
  --namespace ai-employees

# Install Workflow Automation
helm install workflow-automation ../workflow-automation/helm \
  --namespace ai-employees

# Install Reporting Agent
helm install reporting-agent ./helm \
  --namespace ai-employees \
  --set integration.taskManager.enabled=true \
  --set integration.workflowAutomation.enabled=true

# Verify all deployments
kubectl get all -n ai-employees
```

---

### Option 3: Plain Kubernetes Manifests

```bash
cd Phase2-Code/reporting-agent

# Deploy with Kustomize
kubectl apply -k k8s/

# Or apply individually
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/cronjob-daily.yaml
kubectl apply -f k8s/cronjob-weekly.yaml

# Check status
kubectl get pods -l app=reporting-agent
kubectl logs -f deployment/reporting-agent
```

---

### Option 4: Local Kind Cluster

```bash
# Create Kind cluster
cat <<EOF | kind create cluster --name ai-employee --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
EOF

# Deploy with Helm
cd Phase2-Code/reporting-agent
helm install reporting-agent ./helm

# Access via port-forward
kubectl port-forward svc/reporting-agent 8080:8080
```

---

## Configuration

### Environment Variables

Key configuration options:

```bash
# LLM Configuration
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=llama2
LLM_TEMPERATURE=0.7

# Integration URLs
TASK_MANAGER_URL=http://task-manager:8080
WORKFLOW_AUTOMATION_URL=http://workflow-automation:8080

# Report Scheduling
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday
WEEKLY_REPORT_TIME=09:00

# Data Retention
REPORT_RETENTION_DAYS=90
DATA_RETENTION_DAYS=30

# Alerting
ALERT_THRESHOLD_OVERDUE_TASKS=5
ALERT_THRESHOLD_FAILED_WORKFLOWS=3

# Export Formats
EXPORT_FORMATS=markdown,json
DEFAULT_EXPORT_FORMAT=markdown

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Helm Values Customization

```yaml
# Custom report templates
reporting:
  templates:
    daily: "custom-daily-template.md"
    weekly: "custom-weekly-template.md"
  
# Alert configuration
alerts:
  enabled: true
  channels:
    - console
    - log
  thresholds:
    overdueTasks: 5
    failedWorkflows: 3

# Storage configuration
persistence:
  reports:
    size: 10Gi
    retentionDays: 90
  data:
    size: 5Gi
    retentionDays: 30
```

---

## Integration Setup

### With Task Manager

```bash
# Enable Task Manager integration
helm upgrade reporting-agent ./helm \
  --set integration.taskManager.enabled=true \
  --set integration.taskManager.url="http://task-manager:8080"

# Test integration
kubectl exec -it deployment/reporting-agent -- \
  curl http://task-manager:8080/api/v1/tasks
```

### With Workflow Automation

```bash
# Enable Workflow Automation integration
helm upgrade reporting-agent ./helm \
  --set integration.workflowAutomation.enabled=true \
  --set integration.workflowAutomation.url="http://workflow-automation:8080"

# Test integration
kubectl exec -it deployment/reporting-agent -- \
  curl http://workflow-automation:8080/api/v1/workflows/runs
```

---

## Monitoring & Observability

### Health Checks

```bash
# Health endpoint
curl http://localhost:8080/health

# Readiness endpoint
curl http://localhost:8080/ready

# Metrics endpoint (Prometheus format)
curl http://localhost:8080/metrics
```

### Prometheus Integration

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: reporting-agent
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: reporting-agent
  endpoints:
  - port: metrics
    interval: 30s
```

### Logging

```bash
# Follow logs
kubectl logs -f deployment/reporting-agent

# View specific report generation
kubectl logs deployment/reporting-agent | grep "report_generated"

# Check for errors
kubectl logs deployment/reporting-agent | grep ERROR
```

---

## Backup & Recovery

### Backup Reports

```bash
# Create backup of reports volume
kubectl exec deployment/reporting-agent -- tar czf /tmp/reports-backup.tar.gz /app/reports

# Copy to local
kubectl cp reporting-agent-pod:/tmp/reports-backup.tar.gz ./reports-backup.tar.gz
```

### Restore Reports

```bash
# Copy backup to pod
kubectl cp ./reports-backup.tar.gz reporting-agent-pod:/tmp/

# Extract
kubectl exec deployment/reporting-agent -- tar xzf /tmp/reports-backup.tar.gz -C /app/reports
```

---

## Troubleshooting

### Reports Not Generated

```bash
# Check CronJob status
kubectl get cronjobs
kubectl describe cronjob reporting-agent-daily

# Check CronJob history
kubectl get jobs -l cronjob=reporting-agent-daily

# Manual trigger
kubectl create job --from=cronjob/reporting-agent-daily manual-daily-report
```

### Integration Issues

```bash
# Test Task Manager connectivity
kubectl exec -it deployment/reporting-agent -- \
  curl http://task-manager:8080/health

# Test Workflow Automation connectivity
kubectl exec -it deployment/reporting-agent -- \
  curl http://workflow-automation:8080/health

# Check environment variables
kubectl exec deployment/reporting-agent -- env | grep -E '(TASK_MANAGER|WORKFLOW)'
```

### Ollama Issues

```bash
# Check Ollama logs
kubectl logs deployment/ollama

# Verify model is loaded
kubectl exec deployment/ollama -- ollama list

# Pull model manually
kubectl exec deployment/ollama -- ollama pull llama2
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -l app.kubernetes.io/name=reporting-agent

# Check disk usage
kubectl exec deployment/reporting-agent -- df -h /app/reports /app/data

# Clean old reports
kubectl exec deployment/reporting-agent -- find /app/reports -mtime +90 -delete
```

---

## Security Best Practices

1. **Use Secrets for Sensitive Data**

```bash
kubectl create secret generic reporting-agent-secrets \
  --from-literal=api-key=your-secret-key

# Reference in Helm values
secrets:
  apiKey:
    existingSecret: reporting-agent-secrets
    key: api-key
```

2. **Enable RBAC**

Ensure ServiceAccount has minimal permissions (already configured in templates).

3. **Network Policies**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: reporting-agent-netpol
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: reporting-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: task-manager
    - podSelector:
        matchLabels:
          app: workflow-automation
    - podSelector:
        matchLabels:
          app: ollama
```

---

## Upgrading

### Helm Upgrade

```bash
# Upgrade to new version
helm upgrade reporting-agent ./helm \
  --namespace ai-employees \
  --values values-production.yaml

# Rollback if needed
helm rollback reporting-agent 0 -n ai-employees
```

### Zero-Downtime Updates

```bash
# Update with rolling strategy
helm upgrade reporting-agent ./helm \
  --set image.tag=1.1.0 \
  --set updateStrategy.type=RollingUpdate \
  --set updateStrategy.rollingUpdate.maxUnavailable=0
```

---

## Scaling

### Manual Scaling

```bash
# Scale replicas
kubectl scale deployment reporting-agent --replicas=3

# Or via Helm
helm upgrade reporting-agent ./helm --set replicaCount=3
```

### Auto-Scaling

```bash
# Enable HPA
helm upgrade reporting-agent ./helm \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=5
```

---

**For quick start, see [QUICKSTART.md](QUICKSTART.md)**
**For API details, see [API.md](API.md)**
**For integration guide, see [INTEGRATION.md](INTEGRATION.md)**
