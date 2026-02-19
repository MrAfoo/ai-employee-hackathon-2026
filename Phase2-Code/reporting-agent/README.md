# Reporting Agent AI Employee

**Version**: 1.0.0  
**Type**: AI-Powered Reporting and Analytics System

## Overview

The Reporting Agent AI Employee autonomously generates comprehensive reports by collecting data from Task Manager and Workflow Automation systems. It provides daily and weekly insights, detects anomalies, and exports reports in multiple formats.

---

## 🎯 Purpose

This AI Employee autonomously generates reports for the team, summarizing progress, detecting anomalies, and providing actionable insights.

---

## ✨ Capabilities

- ✅ **Automated Data Collection**: Collects task and workflow data from integrated systems
- ✅ **Daily Reports**: Automatically generated at 9 AM every day
- ✅ **Weekly Reports**: Comprehensive summaries every Monday at 9 AM
- ✅ **Multi-Format Export**: Markdown, JSON, and HTML formats
- ✅ **Anomaly Detection**: Automatically identifies issues and missed deadlines
- ✅ **AI-Powered Insights**: Uses LLM for intelligent analysis and recommendations
- ✅ **Data Visualization**: Charts and graphs using Plotly
- ✅ **Alert System**: Sends notifications for critical issues
- ✅ **Transparent Reporting**: All data sources and calculations visible

---

## 📥 Inputs

- **Task Data**: From Task Manager API
  - Task completion rates
  - Overdue tasks
  - Priority distribution
  - Team member performance

- **Workflow Data**: From Workflow Automation API
  - Workflow execution stats
  - Success/failure rates
  - Performance metrics
  - Error logs

---

## 📤 Outputs

- **Daily Reports**: Daily status and progress summaries
- **Weekly Reports**: Comprehensive weekly analytics with trends
- **Anomaly Alerts**: Notifications for detected issues
- **Exported Files**: Reports in Markdown, JSON, and HTML formats
- **Metrics**: Prometheus metrics for monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           Reporting Agent System                │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │        Data Collection Layer              │ │
│  ├──────────────────────────────────────────┤ │
│  │  Task Manager API Client                 │ │
│  │  Workflow Automation API Client          │ │
│  └─────────────┬────────────────────────────┘ │
│                │                                │
│  ┌─────────────▼────────────────────────────┐ │
│  │       Data Processing Layer              │ │
│  ├──────────────────────────────────────────┤ │
│  │  - Aggregation                           │ │
│  │  - Statistical Analysis                  │ │
│  │  - Anomaly Detection                     │ │
│  │  - Trend Analysis                        │ │
│  └─────────────┬────────────────────────────┘ │
│                │                                │
│  ┌─────────────▼────────────────────────────┐ │
│  │         AI Analysis Layer                │ │
│  ├──────────────────────────────────────────┤ │
│  │  Ollama LLM (llama2)                     │ │
│  │  - Insights Generation                   │ │
│  │  - Recommendations                       │ │
│  └─────────────┬────────────────────────────┘ │
│                │                                │
│  ┌─────────────▼────────────────────────────┐ │
│  │       Report Generation Layer            │ │
│  ├──────────────────────────────────────────┤ │
│  │  - Jinja2 Templates                      │ │
│  │  - Markdown Rendering                    │ │
│  │  - JSON Export                           │ │
│  │  - HTML Export (Pandoc)                  │ │
│  └─────────────┬────────────────────────────┘ │
│                │                                │
│  ┌─────────────▼────────────────────────────┐ │
│  │      Persistent Storage (5GB)            │ │
│  │      - Reports Archive                   │ │
│  │      - Historical Data                   │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose OR
- Kubernetes (Kind/Minikube) + Helm
- (Optional) Task Manager and Workflow Automation running

### Docker Compose Deployment

```bash
cd Phase2-Code/reporting-agent
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f reporting-agent
```

### Kubernetes Deployment

```bash
# Using kubectl
kubectl apply -f k8s/

# Using Helm
helm install reporting-agent ./helm

# Check status
kubectl get pods -l app=reporting-agent
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

# Generate a manual report
make generate-report

# View logs
make logs

# Clean up
make clean
```

---

## 📊 Report Examples

### Daily Report Sections

1. **Executive Summary** - AI-generated overview
2. **Task Manager Summary** - Completion rates, overdue tasks, priorities
3. **Workflow Automation Summary** - Execution stats, success rates
4. **Anomalies Detected** - Issues and missed deadlines
5. **Team Performance Metrics** - Productivity and velocity
6. **AI Insights** - LLM-generated analysis
7. **Recommendations** - Actionable suggestions
8. **Next Steps** - Follow-up items

### Weekly Report Sections

All daily sections plus:
- Week-over-week comparisons
- Daily breakdown tables
- Category analysis
- Top contributors
- Failed workflow deep-dive
- Critical issues summary
- Achievements and challenges
- Goals for next week

---

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=llama2

# Application
REPORTING_PORT=8080
REPORTS_DIR=/app/reports

# Integration
TASK_MANAGER_URL=http://task-manager:8080
WORKFLOW_AUTOMATION_URL=http://workflow-automation:8080

# Scheduling
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday

# Formats
REPORT_FORMATS=markdown,json,html
```

See `.env.example` for complete configuration options.

---

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### List Reports
```bash
GET /reports?type=daily&limit=10
```

### Get Latest Report
```bash
GET /reports/latest?type=daily
```

### Get Specific Report
```bash
GET /reports/{report_id}
```

### Generate Report Manually
```bash
POST /reports/generate
Content-Type: application/json

{
  "type": "daily",
  "format": "markdown"
}
```

### Download Report
```bash
GET /reports/{report_id}/download?format=markdown
```

### Get Report Statistics
```bash
GET /stats
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
- `reports_generated_total` - Total reports by type
- `report_generation_duration_seconds` - Generation time
- `anomalies_detected_total` - Anomaly counts
- `integration_requests_total` - API call success/failure

---

## 🎓 Customizing Reports

### Modify Templates

Edit Jinja2 templates in `templates/`:
- `daily-report-template.md`
- `weekly-report-template.md`

### Add Custom Sections

```jinja2
## Custom Section

{{ custom_data }}

{% for item in custom_list %}
- {{ item.name }}: {{ item.value }}
{% endfor %}
```

### Configure Data Sources

Update `config/app-config.yaml`:

```yaml
integrations:
  task_manager:
    enabled: true
    url: "http://task-manager:8080"
  
  custom_service:
    enabled: true
    url: "http://custom:8080"
```

---

## 🔗 Integration

### With Task Manager

```bash
# Set Task Manager URL
export TASK_MANAGER_URL=http://task-manager:8080

# Test connection
curl $TASK_MANAGER_URL/health
```

### With Workflow Automation

```bash
# Set Workflow Automation URL
export WORKFLOW_AUTOMATION_URL=http://workflow-automation:8080

# Test connection
curl $WORKFLOW_AUTOMATION_URL/health
```

### Standalone Mode

Can run without integrations using mock data for testing:

```bash
# Disable integrations
export TASK_MANAGER_ENABLED=false
export WORKFLOW_AUTOMATION_ENABLED=false
```

See `INTEGRATION.md` for detailed integration guide.

---

## 🔒 Security

- Non-root container user
- Dropped Linux capabilities
- Read-only report templates
- API authentication (optional)
- Network policies (Kubernetes)

---

## 📖 Documentation

- **[API.md](API.md)** - Complete REST API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start for judges
- **[INTEGRATION.md](INTEGRATION.md)** - Integration with other AI Employees
- **[Makefile](Makefile)** - Available make commands

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (requires Task Manager/Workflow Automation)
pytest tests/integration/

# Generate a test report
curl -X POST http://localhost:8080/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"type": "daily"}'
```

---

## 📦 Dependencies

See `requirements.txt` for complete list. Key dependencies:

- **FastAPI** - REST API framework
- **Pandas** - Data analysis
- **Plotly** - Data visualization
- **Jinja2** - Template rendering
- **Pandoc** - Format conversion
- **LangChain** - LLM integration
- **httpx** - HTTP client for integrations

---

## 🐛 Troubleshooting

### Reports showing "No Data Available"

1. Check integration URLs are correct
2. Verify Task Manager/Workflow Automation are running
3. Check logs: `kubectl logs -l app=reporting-agent`

### CronJobs not running

1. Check CronJob status: `kubectl get cronjobs`
2. Verify schedule syntax
3. Check timezone settings

### LLM insights not generating

1. Verify Ollama is running: `curl http://ollama:11434/api/tags`
2. Check model is available: `ollama list`
3. Increase LLM timeout

### Reports not persisting

1. Check PVC is bound: `kubectl get pvc`
2. Verify storage class exists
3. Check volume mount permissions

---

## 📄 License

This project is part of the AI Employee Competition submission.

---

## 🎯 Success Criteria

✅ Judges can view reports without extra setup  
✅ Demonstrates autonomy in monitoring and reporting  
✅ Runs locally using free/open-source tools  
✅ Reports are reproducible and transparent  
✅ Deployment reproducible via Docker + Kind/Minikube + Helm

---

**For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**  
**For quick start guide, see [QUICKSTART.md](QUICKSTART.md)**  
**For integration guide, see [INTEGRATION.md](INTEGRATION.md)**