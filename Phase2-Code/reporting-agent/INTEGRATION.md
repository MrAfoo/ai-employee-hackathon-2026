# Reporting Agent Integration Guide

## Overview

The Reporting Agent AI Employee integrates with other AI Employees to collect data and generate comprehensive reports.

---

## Architecture

```
┌─────────────────────┐
│  Task Manager       │
│  AI Employee        │◄─────┐
└─────────────────────┘      │
                              │
┌─────────────────────┐      │  Data Collection
│  Workflow           │      │  via REST API
│  Automation         │◄─────┤
│  AI Employee        │      │
└─────────────────────┘      │
                              │
                        ┌─────┴──────────┐
                        │  Reporting     │
                        │  Agent         │
                        │  AI Employee   │
                        └────────────────┘
                              │
                              │  Generates
                              ▼
                        ┌────────────────┐
                        │  Reports       │
                        │  - Markdown    │
                        │  - JSON        │
                        │  - HTML        │
                        └────────────────┘
```

---

## Integration with Task Manager

### API Endpoints Used

The Reporting Agent calls the following Task Manager endpoints:

- `GET /tasks` - Retrieve all tasks
- `GET /tasks?status=overdue` - Get overdue tasks
- `GET /tasks?priority=high` - Get high-priority tasks
- `GET /stats` - Get task statistics

### Data Collected

- Task completion rates
- Overdue tasks
- Priority distribution
- Team member performance
- Task creation/completion trends

### Configuration

Set the Task Manager URL in environment variables:

```bash
TASK_MANAGER_URL=http://task-manager:8080
TASK_MANAGER_TIMEOUT=30
```

---

## Integration with Workflow Automation

### API Endpoints Used

The Reporting Agent calls the following Workflow Automation endpoints:

- `GET /executions` - Retrieve workflow executions
- `GET /executions?status=failed` - Get failed executions
- `GET /workflows` - List all workflows
- `GET /stats` - Get workflow statistics

### Data Collected

- Workflow execution counts
- Success/failure rates
- Average execution duration
- Failed workflow analysis
- Workflow performance trends

### Configuration

Set the Workflow Automation URL in environment variables:

```bash
WORKFLOW_AUTOMATION_URL=http://workflow-automation:8080
WORKFLOW_AUTOMATION_TIMEOUT=30
```

---

## Deployment Scenarios

### 1. Standalone Deployment

Deploy only the Reporting Agent with mock data:

```bash
docker-compose up -d reporting-agent ollama
```

### 2. Integrated Deployment with Task Manager

```yaml
# docker-compose.override.yaml
services:
  reporting-agent:
    depends_on:
      - task-manager
    environment:
      - TASK_MANAGER_URL=http://task-manager:8080

  task-manager:
    image: task-manager:latest
    ports:
      - "8081:8080"
```

### 3. Full Integration (All AI Employees)

```bash
# Deploy all three AI Employees
cd Phase2-Code

# Start Task Manager
docker-compose -f task-manager/docker-compose.yaml up -d

# Start Workflow Automation
docker-compose -f workflow-automation/docker-compose.yaml up -d

# Start Reporting Agent
docker-compose -f reporting-agent/docker-compose.yaml up -d
```

### 4. Kubernetes Full Stack

```bash
# Deploy all AI Employees in Kubernetes
kubectl apply -f task-manager/k8s/
kubectl apply -f workflow-automation/k8s/
kubectl apply -f reporting-agent/k8s/

# Or using Helm
helm install task-manager task-manager/helm
helm install workflow-automation workflow-automation/helm
helm install reporting-agent reporting-agent/helm
```

---

## Data Flow

### Daily Report Generation

1. **Triggered**: CronJob runs at 09:00 daily
2. **Data Collection**:
   - Fetch tasks from Task Manager API
   - Fetch workflow executions from Workflow Automation API
3. **Analysis**:
   - Calculate completion rates
   - Detect anomalies
   - Identify trends
4. **AI Processing**:
   - Generate insights using LLM
   - Create recommendations
5. **Report Generation**:
   - Render Markdown report
   - Export JSON data
   - Save to persistent storage
6. **Notification**:
   - Send completion alert
   - Log report location

### Weekly Report Generation

Similar to daily reports but with:
- 7-day data aggregation
- Week-over-week comparisons
- Deeper trend analysis
- More comprehensive AI insights

---

## API Response Examples

### Task Manager Response

```json
{
  "tasks": [
    {
      "id": "task-001",
      "name": "Implement authentication",
      "status": "completed",
      "priority": "high",
      "deadline": "2026-02-15",
      "completed_at": "2026-02-14T10:30:00Z"
    }
  ],
  "stats": {
    "total": 45,
    "completed": 38,
    "in_progress": 5,
    "overdue": 2
  }
}
```

### Workflow Automation Response

```json
{
  "executions": [
    {
      "execution_id": "exec-001",
      "workflow_name": "data-backup",
      "status": "completed",
      "duration": "120s",
      "started_at": "2026-02-16T00:00:00Z"
    }
  ],
  "stats": {
    "total": 150,
    "successful": 145,
    "failed": 5,
    "success_rate": 0.967
  }
}
```

---

## Error Handling

### Network Failures

If an integrated service is unavailable:

```python
# Reporting Agent handles gracefully
try:
    task_data = await fetch_task_manager_data()
except httpx.ConnectError:
    logger.warning("Task Manager unavailable, using cached data")
    task_data = load_cached_data("task_manager")
```

### Partial Data

Reports can be generated with partial data:

```
⚠️ Note: Task Manager data unavailable. Report generated with 
available Workflow Automation data only.
```

---

## Testing Integration

### Manual Testing

```bash
# Test Task Manager connection
curl http://task-manager:8080/health

# Test Workflow Automation connection
curl http://workflow-automation:8080/health

# Trigger manual report generation
curl -X POST http://reporting-agent:8080/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"type": "daily"}'
```

### Integration Tests

```bash
# Run integration test suite
cd Phase2-Code/reporting-agent
pytest tests/integration/
```

---

## Monitoring Integration Health

### Metrics Exposed

- `integration_requests_total{service="task-manager",status="success"}`
- `integration_requests_total{service="workflow-automation",status="success"}`
- `integration_response_time_seconds{service="task-manager"}`
- `data_collection_errors_total{service="task-manager"}`

### Health Check

```bash
GET /health
```

Response includes integration status:

```json
{
  "status": "healthy",
  "integrations": {
    "task_manager": {
      "status": "connected",
      "last_check": "2026-02-16T18:30:00Z",
      "latency_ms": 45
    },
    "workflow_automation": {
      "status": "connected",
      "last_check": "2026-02-16T18:30:00Z",
      "latency_ms": 52
    }
  }
}
```

---

## Troubleshooting

### Problem: Reports show "No Data Available"

**Solution**:
1. Check service URLs are correct
2. Verify services are running: `kubectl get pods`
3. Check network connectivity between pods
4. Review logs: `kubectl logs reporting-agent-xxx`

### Problem: Incomplete Reports

**Solution**:
1. Check API timeouts (increase if needed)
2. Verify data format from integrated services
3. Check for API version compatibility

### Problem: Slow Report Generation

**Solution**:
1. Increase timeout values
2. Enable data caching
3. Optimize API queries (use filters)
4. Scale integrated services

---

## Security Considerations

### API Authentication

If integrated services require authentication:

```yaml
# values.yaml
integrations:
  taskManager:
    url: "http://task-manager:8080"
    auth:
      enabled: true
      apiKey: "secret-key"
```

### Network Policies

Restrict network access in Kubernetes:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: reporting-agent-network-policy
spec:
  podSelector:
    matchLabels:
      app: reporting-agent
  policyTypes:
  - Egress
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

## Future Enhancements

- [ ] Real-time data streaming instead of periodic polling
- [ ] GraphQL API for more efficient data fetching
- [ ] Webhook notifications to Reporting Agent on data changes
- [ ] Distributed tracing across all AI Employees
- [ ] Shared message queue for event-driven architecture

---

For more information, see:
- [Task Manager API Documentation](../task-manager/API.md)
- [Workflow Automation API Documentation](../workflow-automation/API.md)
- [Reporting Agent API Documentation](./API.md)
