# Workflow Automation AI Employee

**Version**: 1.0.0  
**Type**: AI-Powered Workflow Orchestration System

## Overview

The Workflow Automation AI Employee is an autonomous system that monitors, triggers, and executes workflows automatically. It reduces manual effort by automating repetitive tasks and provides complete transparency through comprehensive logging.

---

## 🎯 Purpose

This AI Employee autonomously automates repetitive workflows to save time and reduce manual effort for small teams.

---

## ✨ Capabilities

- ✅ **Event-Driven Workflows**: Monitors incoming tasks and triggers workflows automatically
- ✅ **Multiple Trigger Types**: Schedule (cron), events, and webhooks
- ✅ **Script Execution**: Executes predefined scripts or commands
- ✅ **Comprehensive Logging**: Logs all actions for transparency and audit
- ✅ **Status Notifications**: Provides updates when workflows complete
- ✅ **AI-Powered**: Uses LLM for intelligent workflow decisions
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Multi-Step Workflows**: Complex workflows with dependencies

---

## 📥 Inputs

- **Workflow Definitions**: YAML/JSON format workflow configurations
- **Trigger Conditions**: Events, schedules (cron), webhooks
- **Parameters**: Runtime parameters for workflow execution

---

## 📤 Outputs

- **Executed Workflows**: Successfully completed workflow runs
- **Execution Logs**: Detailed logs of all completed actions
- **Notifications**: Success/failure notifications
- **Metrics**: Prometheus metrics for monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          Workflow Automation System             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Scheduler│    │  Event   │    │ Webhook  │ │
│  │ Triggers │    │ Triggers │    │ Triggers │ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘ │
│       │               │               │        │
│       └───────────────┴───────────────┘        │
│                       │                        │
│              ┌────────▼────────┐               │
│              │ Workflow Engine │               │
│              │   (Prefect/     │               │
│              │    Celery)      │               │
│              └────────┬────────┘               │
│                       │                        │
│       ┌───────────────┼───────────────┐        │
│       │               │               │        │
│  ┌────▼─────┐  ┌──────▼──────┐  ┌────▼─────┐ │
│  │  Script  │  │  AI Task    │  │  HTTP    │ │
│  │ Executor │  │  Processor  │  │  Client  │ │
│  └──────────┘  └─────────────┘  └──────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │         Redis (Task Queue)               │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │      Ollama LLM (AI Processing)          │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose OR
- Kubernetes (Kind/Minikube) + Helm

### Docker Compose Deployment (Recommended for Testing)

```bash
cd Phase2-Code/workflow-automation
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f workflow-automation
```

### Kubernetes Deployment

```bash
# Using kubectl
kubectl apply -f k8s/

# Using Helm
helm install workflow-automation ./helm

# Check status
kubectl get pods -l app=workflow-automation
```

### Makefile Commands

```bash
# Build Docker image
make build

# Deploy to Kind
make deploy-kind

# Deploy with Helm
make deploy-helm

# Port forward to access locally
make port-forward

# View logs
make logs

# Clean up
make clean
```

---

## 📋 Example Workflows

### 1. Example Workflow (Demonstrates All Features)

**File**: `workflows/example-workflow.yaml`

**Triggers**:
- Daily at 9 AM (cron)
- On task creation event
- Via webhook at `/trigger/example`

**Steps**:
1. Validate input parameters
2. Process data with retry logic
3. AI analysis using LLM
4. Send notifications

### 2. Data Backup Workflow

**File**: `workflows/data-backup-workflow.yaml`

**Triggers**:
- Daily at midnight

**Steps**:
1. Check disk space
2. Create compressed backup
3. Verify backup integrity
4. Clean up old backups
5. Generate AI report

---

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=llama2

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
```

See `.env.example` for complete configuration options.

---

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### List Workflows
```bash
GET /workflows
```

### Get Workflow Details
```bash
GET /workflows/{workflow_name}
```

### Trigger Workflow
```bash
POST /workflows/{workflow_name}/trigger
Content-Type: application/json

{
  "parameters": {
    "input_data": "custom data"
  }
}
```

### List Executions
```bash
GET /executions?status=running&limit=50
```

### Get Execution Details
```bash
GET /executions/{execution_id}
```

See `API.md` for complete API documentation.

---

## 📊 Monitoring

### Prometheus Metrics

```bash
# Access metrics
curl http://localhost:9090/metrics
```

**Available Metrics**:
- `workflow_executions_total` - Total workflow executions by status
- `workflow_execution_duration_seconds` - Execution duration histogram
- `workflow_step_duration_seconds` - Individual step durations
- `workflow_errors_total` - Error counts by type

### Health Monitoring

```bash
# Check health status
curl http://localhost:8080/health
```

---

## 🎓 Creating Custom Workflows

### Basic Workflow Structure

```yaml
name: my-workflow
description: My custom workflow
version: "1.0"

triggers:
  - type: schedule
    cron: "0 12 * * *"  # Daily at noon
    enabled: true

parameters:
  - name: my_param
    type: string
    required: false
    default: "default value"

steps:
  - name: step1
    type: script
    script: |
      #!/bin/bash
      echo "Hello, {{ params.my_param }}"
    timeout: 60s

  - name: step2
    type: llm
    prompt: "Analyze the following: {{ steps.step1.output }}"
    model: llama2

on_success:
  - type: log
    level: info
    message: "Workflow completed"

on_failure:
  - type: notification
    message: "Workflow failed: {{ error.message }}"
```

### Adding Your Workflow

1. Create YAML file in `workflows/` directory
2. Restart the workflow-automation service
3. Trigger via API or wait for scheduled execution

---

## 🔒 Security

- Non-root container user
- Dropped Linux capabilities
- RBAC for Kubernetes pod management
- Read-only root filesystem (optional)
- Network policies (optional)

---

## 📖 Documentation

- **[API.md](API.md)** - Complete REST API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start for judges
- **[Makefile](Makefile)** - Available make commands

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Test workflow execution
curl -X POST http://localhost:8080/workflows/example-workflow/trigger
```

---

## 📦 Dependencies

See `requirements.txt` for complete list. Key dependencies:

- **FastAPI** - REST API framework
- **Prefect** - Workflow orchestration
- **Celery** - Distributed task queue
- **Redis** - Task queue backend
- **LangChain** - LLM integration
- **APScheduler** - Job scheduling

---

## 🤝 Integration

The Workflow Automation AI Employee can integrate with:

- **Task Manager**: Trigger workflows on task events
- **Reporting Agent**: Provide execution data for reports
- **External Systems**: Via webhooks and HTTP calls

---

## 🐛 Troubleshooting

### Workflows not executing

1. Check Redis connection: `redis-cli ping`
2. Verify cron schedule syntax
3. Check logs: `kubectl logs -l app=workflow-automation`

### LLM steps failing

1. Verify Ollama is running: `curl http://ollama:11434/api/tags`
2. Check model is pulled: `ollama list`
3. Increase timeout for LLM steps

### Performance issues

1. Increase `MAX_CONCURRENT_WORKFLOWS`
2. Scale Redis if needed
3. Add more workflow-automation replicas

---

## 📄 License

This project is part of the AI Employee Competition submission.

---

## 🎯 Success Criteria

✅ Judges can trigger workflows easily  
✅ Demonstrates autonomy in executing tasks without human intervention  
✅ Runs locally using free/open-source tools  
✅ Deployment reproducible via Docker + Kind/Minikube + Helm  
✅ Workflows are documented and transparent

---

**For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**  
**For quick start guide, see [QUICKSTART.md](QUICKSTART.md)**