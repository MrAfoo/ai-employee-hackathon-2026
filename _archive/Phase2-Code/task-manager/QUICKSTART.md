# Task Manager AI Employee - Quick Start

**One-command deployment for judges and evaluators.**

## Prerequisites

- Docker
- Kubernetes (Kind or Minikube)
- kubectl
- Helm 3.x (optional)

## 🚀 Fastest Deployment (Docker Compose)

```bash
docker-compose up -d
```

**That's it!** The Task Manager AI Employee is now running at `http://localhost:8080`

Test it:
```bash
curl http://localhost:8080/health
```

## 🎯 One-Command Kubernetes Deployment

### Option A: Using Helm (Recommended)

```bash
make deploy-helm && make port-forward
```

### Option B: Using kubectl

```bash
make deploy-kind && make port-forward
```

### Option C: Manual Commands

**For Kind:**
```bash
docker build -t task-manager:latest . && \
kind load docker-image task-manager:latest && \
helm install task-manager ./helm
```

**For Minikube:**
```bash
eval $(minikube docker-env) && \
docker build -t task-manager:latest . && \
helm install task-manager ./helm
```

## ✅ Verify Deployment

```bash
# Check pods are running
kubectl get pods

# View logs
kubectl logs -f deployment/task-manager

# Port forward (if not already done)
kubectl port-forward svc/task-manager 8080:8080

# Test health
curl http://localhost:8080/health
```

## 📝 Test the AI Employee

### 1. Create a task
```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review deployment documentation",
    "description": "Ensure all docs are complete",
    "deadline": "2026-02-20T17:00:00Z",
    "priority": "high"
  }'
```

### 2. List all tasks
```bash
curl http://localhost:8080/api/v1/tasks
```

### 3. Get daily report
```bash
curl http://localhost:8080/api/v1/reports/daily
```

### 4. Verify autonomous behavior

The AI Employee automatically:
- ✅ Prioritizes tasks by deadline and importance
- ✅ Generates daily reports at 09:00 (configurable)
- ✅ Flags overdue tasks
- ✅ Suggests corrective actions

Check the CronJob:
```bash
kubectl get cronjobs
kubectl logs job/task-manager-daily-report-<timestamp>
```

## 🧹 Cleanup

**Docker Compose:**
```bash
docker-compose down -v
```

**Kubernetes:**
```bash
make clean
# OR
helm uninstall task-manager
```

## 📚 Next Steps

- See [README.md](README.md) for full API documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment options
- Customize settings in `helm/values.yaml`

## 🎓 For Judges

**Reproduce the entire deployment:**
```bash
# Clone/navigate to the directory
cd Phase2-Code/task-manager

# One command deployment
make deploy-helm && make port-forward

# Test in another terminal
make test-health
make test-create-task
make test-list-tasks
```

**Success criteria met:**
- ✅ One-command reproducible deployment
- ✅ Runs locally with free/open-source tools (Ollama)
- ✅ Demonstrates autonomous task management
- ✅ Works on Kind/Minikube
- ✅ Complete documentation
