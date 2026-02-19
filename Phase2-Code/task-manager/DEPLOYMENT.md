# Task Manager AI Employee - Deployment Guide

This guide provides step-by-step instructions for deploying the Task Manager AI Employee.

## Prerequisites

- Docker installed
- Kubernetes cluster (Kind, Minikube, or other)
- kubectl configured
- Helm 3.x (optional, for Helm deployment)

## Deployment Methods

### Method 1: Docker Compose (Fastest - Local Development)

**Single command deployment:**
```bash
docker-compose up -d
```

**What this does:**
1. Builds the Task Manager image
2. Pulls and runs Ollama for local LLM
3. Creates persistent volumes
4. Starts both services with health checks

**Verify:**
```bash
# Check services are running
docker-compose ps

# View logs
docker-compose logs -f

# Test the API
curl http://localhost:8080/health
```

### Method 2: Kubernetes with kubectl (Standard Manifests)

**Single command deployment:**
```bash
# Build and load image
docker build -t task-manager:latest . && \
kind load docker-image task-manager:latest && \
kubectl apply -k k8s/
```

**Step-by-step:**
```bash
# 1. Build the Docker image
docker build -t task-manager:latest .

# 2. Load into your cluster
# For Kind:
kind load docker-image task-manager:latest

# For Minikube:
eval $(minikube docker-env)
docker build -t task-manager:latest .

# 3. Apply Kubernetes manifests
kubectl apply -k k8s/

# 4. Wait for deployment
kubectl wait --for=condition=ready pod -l app=task-manager --timeout=300s

# 5. Check status
kubectl get all

# 6. Access the service
kubectl port-forward svc/task-manager 8080:8080
```

### Method 3: Helm Chart (Production-Ready)

**Single command deployment:**
```bash
docker build -t task-manager:latest . && \
kind load docker-image task-manager:latest && \
helm install task-manager ./helm
```

**Step-by-step:**
```bash
# 1. Build and load image (same as Method 2)
docker build -t task-manager:latest .
kind load docker-image task-manager:latest

# 2. Install with Helm
helm install task-manager ./helm

# 3. Check installation
helm status task-manager
helm list

# 4. View resources
kubectl get all -l app.kubernetes.io/instance=task-manager

# 5. Access the service
kubectl port-forward svc/task-manager 8080:8080
```

**Customize with values:**
```bash
# Create custom values file
cat > my-values.yaml <<EOF
replicaCount: 2
resources:
  limits:
    memory: 1Gi
env:
  - name: DAILY_REPORT_TIME
    value: "08:00"
EOF

# Install with custom values
helm install task-manager ./helm -f my-values.yaml

# Upgrade existing deployment
helm upgrade task-manager ./helm -f my-values.yaml
```

## Verification Steps

### 1. Check Pod Status
```bash
kubectl get pods
# Should show: task-manager-xxxx-xxxx   1/1   Running
```

### 2. Check Logs
```bash
kubectl logs deployment/task-manager
# Should show: Application started successfully
```

### 3. Test Health Endpoint
```bash
kubectl port-forward svc/task-manager 8080:8080 &
curl http://localhost:8080/health
# Expected: {"status": "healthy"}
```

### 4. Create a Test Task
```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Verify deployment",
    "deadline": "2026-02-20T17:00:00Z",
    "priority": "high"
  }'
```

### 5. Verify Daily Report CronJob
```bash
kubectl get cronjobs
# Should show: task-manager-daily-report

# Manually trigger for testing
kubectl create job --from=cronjob/task-manager-daily-report test-report
kubectl logs job/test-report
```

## Troubleshooting

### Issue: Pods in ImagePullBackOff

**Cause:** Image not loaded into cluster

**Solution:**
```bash
# For Kind
kind load docker-image task-manager:latest

# For Minikube (rebuild in cluster)
eval $(minikube docker-env)
docker build -t task-manager:latest .
```

### Issue: Pods in CrashLoopBackOff

**Diagnosis:**
```bash
kubectl logs deployment/task-manager
kubectl describe pod <pod-name>
```

**Common causes:**
- Missing environment variables
- Storage mount issues
- Application errors

### Issue: PVC Pending

**Diagnosis:**
```bash
kubectl get pvc
kubectl describe pvc task-manager-pvc
```

**Solution:**
```bash
# Check storage class exists
kubectl get storageclass

# Use different storage class
helm install task-manager ./helm \
  --set persistence.storageClass=hostpath
```

### Issue: Service Not Accessible

**Check service:**
```bash
kubectl get svc task-manager
kubectl describe svc task-manager
```

**Check endpoints:**
```bash
kubectl get endpoints task-manager
```

**Port forward:**
```bash
kubectl port-forward svc/task-manager 8080:8080
```

## Cleanup

### Docker Compose
```bash
docker-compose down -v
```

### Kubernetes (kubectl)
```bash
kubectl delete -k k8s/
```

### Helm
```bash
helm uninstall task-manager
kubectl delete pvc task-manager-pvc  # If persistence was enabled
```

## Performance Tuning

### Adjust Resources
```bash
# Helm
helm upgrade task-manager ./helm \
  --set resources.limits.cpu=1000m \
  --set resources.limits.memory=1Gi

# kubectl (edit deployment)
kubectl edit deployment task-manager
```

### Scale Replicas
```bash
# Helm
helm upgrade task-manager ./helm --set replicaCount=3

# kubectl
kubectl scale deployment task-manager --replicas=3
```

### Enable Autoscaling
```bash
helm upgrade task-manager ./helm \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=1 \
  --set autoscaling.maxReplicas=5
```

## Production Considerations

1. **Ingress**: Enable ingress in Helm values for external access
2. **TLS**: Configure TLS certificates for secure communication
3. **Monitoring**: Add Prometheus metrics and Grafana dashboards
4. **Backup**: Configure PVC snapshots for data backup
5. **High Availability**: Use multiple replicas with pod anti-affinity
6. **Resource Limits**: Set appropriate CPU/memory limits
7. **Security**: Use network policies and RBAC

## Next Steps

1. ✅ Deploy the application
2. Create test tasks via API
3. Verify daily reports are generated
4. Customize configuration for your team
5. Set up monitoring and alerts
6. Document team-specific workflows
