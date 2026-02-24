# Task Manager AI Employee

An autonomous AI employee that manages tasks, deadlines, and priorities for small teams.

## Features

- ✅ Accept tasks via CLI or REST API
- ✅ Prioritize tasks based on deadlines and importance
- ✅ Provide daily status updates automatically
- ✅ Flag overdue tasks and suggest corrective actions
- ✅ Run locally using free/open-source tools
- ✅ Reproducible deployment via Docker, Kubernetes, and Helm

## Architecture

- **Backend**: Python FastAPI with SQLAlchemy for persistence
- **AI/LLM**: Ollama for local LLM inference (llama2 model)
- **Scheduling**: APScheduler for daily reports and automated tasks
- **Storage**: Persistent volumes for task data
- **API**: REST API for task management

## Quick Start

### Option 1: Docker Compose (Recommended for Local Development)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f task-manager

# Access the API
curl http://localhost:8080/health
```

### Option 2: Kubernetes with kubectl (Plain Manifests)

```bash
# Build the Docker image
docker build -t task-manager:latest .

# Load image into Kind/Minikube
kind load docker-image task-manager:latest
# OR for Minikube:
# minikube image load task-manager:latest

# Apply Kubernetes manifests
kubectl apply -k k8s/

# Check deployment status
kubectl get pods
kubectl logs deployment/task-manager

# Port forward to access locally
kubectl port-forward svc/task-manager 8080:8080
```

### Option 3: Helm Chart (Production-Ready)

```bash
# Build the Docker image
docker build -t task-manager:latest .

# Load image into Kind/Minikube
kind load docker-image task-manager:latest

# Install with Helm
helm install task-manager ./helm

# Check status
helm status task-manager
kubectl get pods

# Port forward to access
kubectl port-forward svc/task-manager 8080:8080

# Upgrade configuration
helm upgrade task-manager ./helm --set replicaCount=2

# Uninstall
helm uninstall task-manager
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### Create Task
```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive docs for the project",
    "deadline": "2026-02-20T17:00:00Z",
    "priority": "high"
  }'
```

### List Tasks
```bash
curl http://localhost:8080/api/v1/tasks
```

### Get Daily Report
```bash
curl http://localhost:8080/api/v1/reports/daily
```

### Get Task by ID
```bash
curl http://localhost:8080/api/v1/tasks/{task_id}
```

### Update Task
```bash
curl -X PUT http://localhost:8080/api/v1/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

### Delete Task
```bash
curl -X DELETE http://localhost:8080/api/v1/tasks/{task_id}
```

## CLI Usage

```bash
# Add a task
docker exec task-manager python -m src.cli add-task \
  --title "Review pull requests" \
  --deadline "2026-02-17" \
  --priority high

# List all tasks
docker exec task-manager python -m src.cli list-tasks

# Generate daily report
docker exec task-manager python -m src.cli generate-daily-report

# Mark task as complete
docker exec task-manager python -m src.cli complete-task --id 1
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://ollama:11434` | Base URL for LLM API |
| `LLM_MODEL` | `llama2` | LLM model to use |
| `TASK_MANAGER_PORT` | `8080` | API server port |
| `TASK_MANAGER_DATA_DIR` | `/app/data` | Data persistence directory |
| `DAILY_REPORT_TIME` | `09:00` | Time for daily report generation |
| `LOG_LEVEL` | `INFO` | Logging level |

### Helm Values

Edit `helm/values.yaml` to customize:
- Resource limits/requests
- Replica count
- Persistence settings
- Environment variables
- Ingress configuration

## Daily Reports

The system automatically generates daily reports at 09:00 (configurable). Reports include:
- Task summary (total, completed, pending, overdue)
- Overdue tasks with corrective action suggestions
- Tasks by priority
- Upcoming deadlines

Reports are available via:
1. API endpoint: `/api/v1/reports/daily`
2. CronJob logs: `kubectl logs job/task-manager-daily-report-<timestamp>`
3. Stored in data directory as JSON/Markdown

## Development

### Project Structure
```
task-manager/
├── Dockerfile              # Container image definition
├── docker-compose.yaml     # Local development setup
├── requirements.txt        # Python dependencies
├── helm/                   # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── pvc.yaml
│       ├── cronjob.yaml
│       └── _helpers.tpl
├── k8s/                    # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── pvc.yaml
│   ├── cronjob.yaml
│   └── kustomization.yaml
└── src/                    # Application source code
    ├── main.py
    ├── cli.py
    └── ...
```

### Testing the Deployment

```bash
# Test with Kind
kind create cluster --name task-manager-test
docker build -t task-manager:latest .
kind load docker-image task-manager:latest --name task-manager-test
helm install task-manager ./helm
kubectl port-forward svc/task-manager 8080:8080

# Test with Minikube
minikube start
eval $(minikube docker-env)
docker build -t task-manager:latest .
helm install task-manager ./helm
minikube service task-manager
```

## Success Criteria

✅ **One-Command Deployment**: Judges can deploy with `helm install task-manager ./helm` or `kubectl apply -k k8s/`

✅ **Autonomous Operation**: AI employee automatically:
- Prioritizes tasks based on deadlines and importance
- Generates daily reports at scheduled time
- Flags overdue tasks with corrective action suggestions

✅ **Local Execution**: Uses Ollama for local LLM inference, no external API dependencies

✅ **Reproducible**: Works on Kind/Minikube with standard storage classes

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Storage issues
```bash
kubectl get pvc
kubectl describe pvc task-manager-pvc
```

### Image pull errors
Make sure to load the image into your cluster:
```bash
kind load docker-image task-manager:latest
# OR
minikube image load task-manager:latest
```

### LLM connection issues
Verify Ollama is running and accessible:
```bash
kubectl port-forward svc/ollama 11434:11434
curl http://localhost:11434/api/version
```

## License

Open source - free to use and modify.
