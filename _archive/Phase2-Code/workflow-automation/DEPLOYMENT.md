# Workflow Automation AI Employee - Deployment Guide

**Comprehensive deployment instructions for production and development environments.**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Helm Deployment](#helm-deployment)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** 20.10+ and Docker Compose 2.0+
- **Kubernetes** 1.24+ (Kind, Minikube, or any K8s cluster)
- **kubectl** configured to access your cluster
- **Helm** 3.x (for Helm deployments)
- **make** (optional, for convenience commands)

### Optional

- **Ollama** (for local LLM, or use the bundled container)
- **Redis** (bundled in deployments)

---

## Docker Deployment

### Method 1: Docker Compose (Recommended for Testing)

```bash
cd Phase2-Code/workflow-automation

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f workflow-automation

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Method 2: Standalone Docker

```bash
# Build image
docker build -t workflow-automation:latest .

# Run Redis
docker run -d --name redis -p 6379:6379 redis:latest

# Run Ollama
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest

# Pull LLM model
docker exec ollama ollama pull llama2

# Run workflow-automation
docker run -d \
  --name workflow-automation \
  -p 8080:8080 \
  -e LLM_BASE_URL=http://ollama:11434 \
  -e REDIS_URL=redis://redis:6379/0 \
  --link redis:redis \
  --link ollama:ollama \
  workflow-automation:latest
```

---

## Kubernetes Deployment

### Method 1: Using kubectl with Kustomize

```bash
cd Phase2-Code/workflow-automation

# Deploy all resources
kubectl apply -k k8s/

# Check deployment status
kubectl get pods -l app=workflow-automation
kubectl get svc workflow-automation

# View logs
kubectl logs -f deployment/workflow-automation

# Port forward to access locally
kubectl port-forward svc/workflow-automation 8080:8080

# Delete resources
kubectl delete -k k8s/
```

### Method 2: Deploy Individual Manifests

```bash
# Deploy in order
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

---

## Helm Deployment

### Installation

```bash
cd Phase2-Code/workflow-automation

# Install with default values
helm install workflow-automation ./helm

# Install with custom values
helm install workflow-automation ./helm \
  --set replicaCount=2 \
  --set workflow.maxConcurrent=10

# Install from custom values file
helm install workflow-automation ./helm -f custom-values.yaml
```

### Upgrade

```bash
# Upgrade deployment
helm upgrade workflow-automation ./helm

# Upgrade with new values
helm upgrade workflow-automation ./helm --set workflow.maxConcurrent=10
```

### Uninstall

```bash
# Remove deployment
helm uninstall workflow-automation

# Remove deployment and PVCs
helm uninstall workflow-automation
kubectl delete pvc -l app.kubernetes.io/name=workflow-automation
```

### Helm Configuration Options

Edit `helm/values.yaml` or use `--set` flags:

```yaml
# Number of replicas
replicaCount: 1

# Container image
image:
  repository: workflow-automation
  tag: latest
  pullPolicy: IfNotPresent

# Resource limits
resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

# Workflow configuration
workflow:
  maxConcurrent: 5
  timeout: 3600
  retryAttempts: 3

# Redis configuration
redis:
  enabled: true
  persistence:
    enabled: true
    size: 2Gi

# Ollama LLM configuration
ollama:
  enabled: true
  model: llama2
```

---

## Configuration

### Environment Variables

Create `.env` file or set in deployment:

```bash
# LLM Configuration
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=llama2
LLM_TEMPERATURE=0.7

# Application
WORKFLOW_PORT=8080
WORKFLOW_DATA_DIR=/app/data
WORKFLOW_LOG_DIR=/app/logs

# Redis
REDIS_URL=redis://redis:6379/0

# Workflow Engine
MAX_CONCURRENT_WORKFLOWS=5
WORKFLOW_TIMEOUT=3600
WORKFLOW_RETRY_ATTEMPTS=3

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Workflow Definitions

Place workflow YAML files in:
- **Docker**: Mount to `/app/workflows`
- **Kubernetes**: ConfigMap or PersistentVolume

Example ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-definitions
data:
  my-workflow.yaml: |
    name: my-workflow
    description: Custom workflow
    triggers:
      - type: schedule
        cron: "0 12 * * *"
    steps:
      - name: step1
        type: script
        script: echo "Hello World"
```

---

## Verification

### Health Check

```bash
# Check health endpoint
curl http://localhost:8080/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "redis": "connected",
    "llm": "available"
  }
}
```

### Test Workflow Execution

```bash
# List available workflows
curl http://localhost:8080/workflows

# Trigger example workflow
curl -X POST http://localhost:8080/workflows/example-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"input_data": "test"}}'

# Check execution status
curl http://localhost:8080/executions/{execution_id}
```

### Check Kubernetes Resources

```bash
# Check all resources
kubectl get all -l app=workflow-automation

# Check persistent volumes
kubectl get pvc

# Check logs
kubectl logs -f deployment/workflow-automation

# Check CronJobs (if any)
kubectl get cronjobs
```

---

## Troubleshooting

### Workflows Not Executing

**Issue**: Workflows are not being triggered

**Solutions**:
1. Check Redis connection:
   ```bash
   kubectl exec -it deployment/workflow-automation -- redis-cli -h redis ping
   ```

2. Verify workflow definitions:
   ```bash
   kubectl exec -it deployment/workflow-automation -- ls -la /app/workflows
   ```

3. Check scheduler logs:
   ```bash
   kubectl logs -f deployment/workflow-automation | grep scheduler
   ```

### LLM Steps Failing

**Issue**: AI-powered steps are failing

**Solutions**:
1. Verify Ollama is running:
   ```bash
   curl http://ollama:11434/api/tags
   ```

2. Check if model is loaded:
   ```bash
   kubectl exec -it deployment/ollama -- ollama list
   ```

3. Pull model if missing:
   ```bash
   kubectl exec -it deployment/ollama -- ollama pull llama2
   ```

### Pod Crashes or OOMKilled

**Issue**: Pods are crashing or being OOM killed

**Solutions**:
1. Increase memory limits in `helm/values.yaml`:
   ```yaml
   resources:
     limits:
       memory: 4Gi
   ```

2. Reduce concurrent workflows:
   ```bash
   helm upgrade workflow-automation ./helm \
     --set workflow.maxConcurrent=3
   ```

### Storage Issues

**Issue**: PVC not binding or full

**Solutions**:
1. Check PVC status:
   ```bash
   kubectl describe pvc workflow-automation-data-pvc
   ```

2. Verify storage class exists:
   ```bash
   kubectl get storageclass
   ```

3. Create storage class if needed (Kind):
   ```yaml
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: standard
   provisioner: rancher.io/local-path
   ```

### Redis Connection Issues

**Issue**: Cannot connect to Redis

**Solutions**:
1. Check Redis pod status:
   ```bash
   kubectl get pods -l app=redis
   ```

2. Test Redis connectivity:
   ```bash
   kubectl run redis-test --rm -it --image=redis -- redis-cli -h redis ping
   ```

3. Verify service exists:
   ```bash
   kubectl get svc redis
   ```

---

## Advanced Configuration

### Custom Workflow Definitions Volume

Mount your own workflow directory:

```yaml
# In helm/values.yaml
persistence:
  workflows:
    enabled: true
    existingClaim: my-workflows-pvc
    mountPath: /app/workflows
```

### External Redis

Use existing Redis instance:

```yaml
# In helm/values.yaml
redis:
  enabled: false

env:
  - name: REDIS_URL
    value: "redis://my-redis.external:6379/0"
```

### Enable Ingress

```yaml
# In helm/values.yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: workflow-automation.local
      paths:
        - path: /
          pathType: Prefix
```

---

## Production Considerations

### High Availability

```yaml
# In helm/values.yaml
replicaCount: 3

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: workflow-automation
          topologyKey: kubernetes.io/hostname
```

### Monitoring

Enable Prometheus monitoring:

```yaml
# In helm/values.yaml
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
```

### Security

1. Enable authentication:
   ```yaml
   env:
     - name: ENABLE_AUTH
       value: "true"
     - name: API_KEY
       valueFrom:
         secretKeyRef:
           name: workflow-automation-secrets
           key: api-key
   ```

2. Use NetworkPolicies:
   ```yaml
   networkPolicy:
     enabled: true
     policyTypes:
       - Ingress
       - Egress
   ```

---

## Scaling

### Horizontal Scaling

```bash
# Scale deployment
kubectl scale deployment workflow-automation --replicas=5

# Or with Helm
helm upgrade workflow-automation ./helm --set replicaCount=5
```

### Vertical Scaling

```bash
# Increase resources
helm upgrade workflow-automation ./helm \
  --set resources.limits.cpu=2000m \
  --set resources.limits.memory=4Gi
```

---

## Backup and Recovery

### Backup Workflow Data

```bash
# Backup PVC data
kubectl exec -it deployment/workflow-automation -- tar czf /tmp/backup.tar.gz /app/data
kubectl cp workflow-automation-<pod-id>:/tmp/backup.tar.gz ./backup.tar.gz
```

### Restore Data

```bash
# Restore from backup
kubectl cp ./backup.tar.gz workflow-automation-<pod-id>:/tmp/backup.tar.gz
kubectl exec -it deployment/workflow-automation -- tar xzf /tmp/backup.tar.gz -C /
```

---

## Next Steps

- Review [API.md](API.md) for API documentation
- See [README.md](README.md) for feature overview
- Check [QUICKSTART.md](QUICKSTART.md) for quick testing
- Customize workflows in `workflows/` directory

---

**For support or questions, please refer to the project documentation.**
