# Workflow Automation AI Employee - Quick Start Guide

Get the Workflow Automation AI Employee running in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- OR Kubernetes cluster (Kind/Minikube) + Helm 3+
- 4GB RAM minimum
- 10GB disk space

## Option 1: Docker Compose (Fastest! ⚡)

### 1. Start the Stack

```bash
cd Phase2-Code/workflow-automation
docker-compose up -d
```

This starts:
- **Workflow Automation** on http://localhost:8080
- **Redis** for task queue
- **Ollama** with Llama2 model

### 2. Wait for Ollama Model Download (~2 minutes)

```bash
docker-compose logs -f ollama
# Wait for "success" message
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8080/health

# List available workflows
curl http://localhost:8080/workflows

# Trigger example workflow
curl -X POST http://localhost:8080/workflows/example-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"input_data": "Hello Workflow!"}}'
```

### 4. View Logs

```bash
# Follow workflow execution
docker-compose logs -f workflow-automation

# Check specific workflow run
curl http://localhost:8080/workflows/runs/<run_id>
```

### 5. Stop Everything

```bash
docker-compose down
# Or keep data: docker-compose down -v
```

---

## Option 2: Kubernetes with Helm

### 1. Setup Kind Cluster (if needed)

```bash
kind create cluster --name ai-employee
```

### 2. Deploy with Helm

```bash
cd Phase2-Code/workflow-automation

# Install the chart
helm install workflow-automation ./helm

# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=workflow-automation --timeout=120s
```

### 3. Access the Service

```bash
# Port forward
kubectl port-forward svc/workflow-automation 8080:8080

# In another terminal, test
curl http://localhost:8080/health
```

### 4. View Workflows

```bash
# Get pod name
POD=$(kubectl get pod -l app.kubernetes.io/name=workflow-automation -o jsonpath='{.items[0].metadata.name}')

# View logs
kubectl logs -f $POD

# List workflows
curl http://localhost:8080/workflows
```

---

## Option 3: Plain Kubernetes

### Quick Deploy

```bash
cd Phase2-Code/workflow-automation

# Apply all resources
kubectl apply -k k8s/

# Check status
kubectl get all -l app=workflow-automation

# Port forward
kubectl port-forward svc/workflow-automation 8080:8080
```

---

## Quick Test Workflows

### 1. Trigger Example Workflow

```bash
curl -X POST http://localhost:8080/workflows/example-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "input_data": "Test data",
      "priority": "high"
    }
  }'
```

### 2. Trigger Data Backup Workflow

```bash
curl -X POST http://localhost:8080/workflows/data-backup-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "source_path": "/app/data",
      "backup_location": "/app/backups"
    }
  }'
```

### 3. Monitor Workflow Execution

```bash
# Get all workflow runs
curl http://localhost:8080/workflows/runs

# Get specific run status
curl http://localhost:8080/workflows/runs/<run_id>

# Get workflow metrics
curl http://localhost:8080/metrics
```

---

## Create Your Own Workflow

### 1. Create Workflow Definition

Create `workflows/my-workflow.yaml`:

```yaml
name: my-workflow
description: My custom workflow
version: "1.0"

triggers:
  - type: api
    enabled: true
  - type: schedule
    cron: "0 */6 * * *"
    enabled: false

parameters:
  - name: target
    type: string
    required: true
    description: Target to process

steps:
  - name: validate-input
    type: script
    script: |
      echo "Validating input: {{ target }}"
      # Your validation logic
    
  - name: process-data
    type: script
    script: |
      echo "Processing: {{ target }}"
      # Your processing logic
    
  - name: notify-complete
    type: notification
    message: "Workflow completed for {{ target }}"

on_success:
  - type: notification
    message: "✅ my-workflow succeeded!"

on_failure:
  - type: notification
    message: "❌ my-workflow failed!"
```

### 2. Mount the Workflow (Docker Compose)

Add to `docker-compose.yaml`:

```yaml
services:
  workflow-automation:
    volumes:
      - ./workflows/my-workflow.yaml:/app/workflows/my-workflow.yaml
```

### 3. Reload and Test

```bash
docker-compose restart workflow-automation

# Trigger your workflow
curl -X POST http://localhost:8080/workflows/my-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"target": "my-data"}}'
```

---

## Troubleshooting

### Workflow Not Running?

```bash
# Check logs
docker-compose logs workflow-automation

# Check Redis connection
docker-compose exec workflow-automation env | grep REDIS
```

### Ollama Model Issues?

```bash
# Download model manually
docker-compose exec ollama ollama pull llama2

# Verify model
docker-compose exec ollama ollama list
```

### Port Already in Use?

Edit `docker-compose.yaml`:

```yaml
ports:
  - "8081:8080"  # Change host port
```

---

## Next Steps

- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- 📊 View [API.md](API.md) for complete API reference
- 🔗 See [INTEGRATION.md] for integrating with Task Manager & Reporting Agent
- 📝 Check [README.md](README.md) for architecture details

---

## Clean Up

### Docker Compose

```bash
docker-compose down -v  # Removes volumes too
```

### Kubernetes

```bash
helm uninstall workflow-automation
# OR
kubectl delete -k k8s/
```

### Kind Cluster

```bash
kind delete cluster --name ai-employee
```

---

**🎉 You're all set! Your Workflow Automation AI Employee is running autonomously.**
