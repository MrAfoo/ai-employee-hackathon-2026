# Reporting Agent AI Employee - Quick Start Guide

Get the Reporting Agent running and generating reports in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- OR Kubernetes cluster (Kind/Minikube) + Helm 3+
- 4GB RAM minimum
- 10GB disk space

## Option 1: Docker Compose (Fastest! ⚡)

### 1. Start the Stack

```bash
cd Phase2-Code/reporting-agent
docker-compose up -d
```

This starts:
- **Reporting Agent** on http://localhost:8080
- **Ollama** with Llama2 model for AI analysis

### 2. Wait for Ollama Model Download (~2 minutes)

```bash
docker-compose logs -f ollama
# Wait for "success" message
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Get report status
curl http://localhost:8080/api/v1/reports/status

# Generate a manual daily report
curl -X POST http://localhost:8080/api/v1/reports/daily/generate
```

### 4. View Generated Reports

```bash
# List all reports
curl http://localhost:8080/api/v1/reports

# Get latest daily report (Markdown)
curl http://localhost:8080/api/v1/reports/daily/latest

# Get latest daily report (JSON)
curl http://localhost:8080/api/v1/reports/daily/latest?format=json

# Access reports directory
docker-compose exec reporting-agent ls -la /app/reports/
```

### 5. Check Logs

```bash
# Follow report generation
docker-compose logs -f reporting-agent

# View specific log entries
docker-compose logs reporting-agent | grep "report_generated"
```

### 6. Stop Everything

```bash
docker-compose down
# Keep data: docker-compose down
# Remove all data: docker-compose down -v
```

---

## Option 2: Kubernetes with Helm

### 1. Setup Kind Cluster (if needed)

```bash
kind create cluster --name ai-employee
```

### 2. Deploy with Helm

```bash
cd Phase2-Code/reporting-agent

# Install the chart
helm install reporting-agent ./helm

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=reporting-agent --timeout=120s
```

### 3. Access the Service

```bash
# Port forward
kubectl port-forward svc/reporting-agent 8080:8080

# In another terminal, test
curl http://localhost:8080/health
```

### 4. Generate Reports

```bash
# Manual daily report
curl -X POST http://localhost:8080/api/v1/reports/daily/generate

# Manual weekly report
curl -X POST http://localhost:8080/api/v1/reports/weekly/generate

# View reports
kubectl exec -it deployment/reporting-agent -- ls -la /app/reports/
```

---

## Option 3: Plain Kubernetes

### Quick Deploy

```bash
cd Phase2-Code/reporting-agent

# Apply all resources
kubectl apply -k k8s/

# Check status
kubectl get all -l app=reporting-agent

# Port forward
kubectl port-forward svc/reporting-agent 8080:8080
```

---

## Quick Test: Generate Reports

### 1. Generate Daily Report

```bash
curl -X POST http://localhost:8080/api/v1/reports/daily/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["task-manager", "workflow-automation"],
    "include_ai_insights": true
  }'
```

Response:
```json
{
  "report_id": "daily-2026-02-16",
  "status": "generated",
  "formats": ["markdown", "json"],
  "timestamp": "2026-02-16T09:00:00Z"
}
```

### 2. View the Report

```bash
# Get Markdown version
curl http://localhost:8080/api/v1/reports/daily-2026-02-16

# Get JSON version
curl http://localhost:8080/api/v1/reports/daily-2026-02-16?format=json

# Download report
curl http://localhost:8080/api/v1/reports/daily-2026-02-16/download \
  -o daily-report.md
```

### 3. Generate Weekly Report

```bash
curl -X POST http://localhost:8080/api/v1/reports/weekly/generate \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 7,
    "year": 2026,
    "include_charts": true
  }'
```

### 4. Get Report Statistics

```bash
# Overall stats
curl http://localhost:8080/api/v1/reports/stats

# Task statistics
curl http://localhost:8080/api/v1/reports/stats/tasks

# Workflow statistics
curl http://localhost:8080/api/v1/reports/stats/workflows
```

---

## Integration with Other AI Employees

### With Task Manager Running

```bash
# Start Task Manager first
cd ../task-manager
docker-compose up -d

# Start Reporting Agent with integration
cd ../reporting-agent
docker-compose up -d

# Generate report with task data
curl -X POST http://localhost:8080/api/v1/reports/daily/generate \
  -d '{"sources": ["task-manager"]}'

# View task insights
curl http://localhost:8080/api/v1/reports/insights/tasks
```

### With Workflow Automation Running

```bash
# Start Workflow Automation first
cd ../workflow-automation
docker-compose up -d

# Start Reporting Agent
cd ../reporting-agent
docker-compose up -d

# Generate report with workflow data
curl -X POST http://localhost:8080/api/v1/reports/daily/generate \
  -d '{"sources": ["workflow-automation"]}'

# View workflow insights
curl http://localhost:8080/api/v1/reports/insights/workflows
```

### Full Stack Integration

```bash
# Start all services
cd Phase2-Code
cd task-manager && docker-compose up -d && cd ..
cd workflow-automation && docker-compose up -d && cd ..
cd reporting-agent && docker-compose up -d && cd ..

# Generate comprehensive report
curl -X POST http://localhost:8080/api/v1/reports/daily/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["task-manager", "workflow-automation"],
    "include_ai_insights": true,
    "include_charts": true
  }'
```

---

## Automated Report Generation

Reports are automatically generated via CronJobs:

- **Daily Report**: 9:00 AM every day
- **Weekly Report**: 9:00 AM every Monday

### View Scheduled Reports

```bash
# Check CronJob status (Kubernetes)
kubectl get cronjobs

# View last daily report run
kubectl get jobs -l cronjob=reporting-agent-daily

# View last weekly report run
kubectl get jobs -l cronjob=reporting-agent-weekly
```

### Manually Trigger Scheduled Jobs

```bash
# Trigger daily report
kubectl create job --from=cronjob/reporting-agent-daily manual-daily-1

# Trigger weekly report
kubectl create job --from=cronjob/reporting-agent-weekly manual-weekly-1

# View job logs
kubectl logs job/manual-daily-1
```

---

## View Sample Reports

### Sample Daily Report Structure

```markdown
# Daily Report - February 16, 2026

## Executive Summary
- **Total Tasks**: 25 (5 completed today)
- **Overdue Tasks**: 3 ⚠️
- **Workflows Executed**: 12 (11 successful, 1 failed)
- **Overall Health**: 🟢 Good

## Task Status
### Completed Today (5)
- ✅ Implement user authentication
- ✅ Fix database connection bug
- ✅ Update documentation

### Overdue Tasks (3)
- ⚠️ Deploy to production (2 days overdue)
- ⚠️ Security audit (1 day overdue)

## Workflow Analysis
### Successful Workflows (11)
- data-backup-workflow: 4 executions
- example-workflow: 7 executions

### Failed Workflows (1)
- ❌ data-backup-workflow: Disk space insufficient

## AI Insights
📊 The team is making good progress with 20% task completion rate.
⚠️ Attention needed: 3 tasks are overdue and may impact deadlines.
💡 Recommendation: Consider prioritizing overdue tasks.

## Alerts
- 🔴 CRITICAL: data-backup-workflow failed due to disk space
- 🟡 WARNING: 3 tasks are overdue
```

### Sample Report via API

```bash
# Get today's report
curl http://localhost:8080/api/v1/reports/daily/latest | less

# Get specific date report
curl http://localhost:8080/api/v1/reports/daily/2026-02-15 | less

# Download as file
curl http://localhost:8080/api/v1/reports/daily/latest/download \
  -o report.md
```

---

## Custom Report Templates

### 1. Create Custom Template

Create `templates/my-custom-template.md`:

```markdown
# Custom Report - {{ date }}

## My Custom Sections

### Tasks
{{ tasks_summary }}

### Workflows
{{ workflows_summary }}

### Custom Insights
{{ ai_insights }}
```

### 2. Use Custom Template (Docker Compose)

Mount the template:

```yaml
services:
  reporting-agent:
    volumes:
      - ./templates/my-custom-template.md:/app/templates/custom-template.md
```

### 3. Generate with Custom Template

```bash
docker-compose restart reporting-agent

curl -X POST http://localhost:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template": "custom-template",
    "output_format": "markdown"
  }'
```

---

## Monitoring & Alerts

### Check Alert Status

```bash
# Get current alerts
curl http://localhost:8080/api/v1/alerts

# Get alert history
curl http://localhost:8080/api/v1/alerts/history

# Get anomalies detected
curl http://localhost:8080/api/v1/alerts/anomalies
```

### Configure Alert Thresholds

Edit `.env`:

```bash
ALERT_THRESHOLD_OVERDUE_TASKS=5
ALERT_THRESHOLD_FAILED_WORKFLOWS=3
ALERT_THRESHOLD_TASK_COMPLETION_RATE=0.5
```

---

## Export Formats

### Export as Markdown

```bash
curl http://localhost:8080/api/v1/reports/daily/latest?format=markdown
```

### Export as JSON

```bash
curl http://localhost:8080/api/v1/reports/daily/latest?format=json
```

### Export as PDF (if Pandoc configured)

```bash
curl http://localhost:8080/api/v1/reports/daily/latest?format=pdf \
  -o report.pdf
```

---

## Troubleshooting

### No Reports Generated?

```bash
# Check logs
docker-compose logs reporting-agent

# Check CronJob (K8s)
kubectl describe cronjob reporting-agent-daily

# Manual trigger
curl -X POST http://localhost:8080/api/v1/reports/daily/generate
```

### Integration Not Working?

```bash
# Test Task Manager connection
docker-compose exec reporting-agent curl http://task-manager:8080/health

# Test Workflow Automation connection
docker-compose exec reporting-agent curl http://workflow-automation:8080/health

# Check environment variables
docker-compose exec reporting-agent env | grep -E '(TASK_MANAGER|WORKFLOW)'
```

### Ollama Model Issues?

```bash
# Download model manually
docker-compose exec ollama ollama pull llama2

# Verify model
docker-compose exec ollama ollama list

# Check Ollama logs
docker-compose logs ollama
```

### Reports Directory Empty?

```bash
# Check volume mount
docker-compose exec reporting-agent ls -la /app/reports/

# Check permissions
docker-compose exec reporting-agent ls -ld /app/reports/

# Manual report generation
curl -X POST http://localhost:8080/api/v1/reports/daily/generate
```

---

## Next Steps

- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- 📊 View [API.md](API.md) for complete API reference
- 🔗 See [INTEGRATION.md](INTEGRATION.md) for multi-service setup
- 📝 Check [README.md](README.md) for architecture details

---

## Clean Up

### Docker Compose

```bash
docker-compose down -v  # Removes volumes too
```

### Kubernetes

```bash
helm uninstall reporting-agent
# OR
kubectl delete -k k8s/
```

### Kind Cluster

```bash
kind delete cluster --name ai-employee
```

---

**🎉 You're all set! Your Reporting Agent is autonomously generating reports.**
