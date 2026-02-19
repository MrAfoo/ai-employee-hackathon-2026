# Reporting Agent AI Employee - API Reference

Complete API documentation for the Reporting Agent AI Employee.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

Currently using optional API key authentication.

```bash
# With API key (if enabled)
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/v1/reports
```

---

## Table of Contents

1. [Health & Status](#health--status)
2. [Reports](#reports)
3. [Report Generation](#report-generation)
4. [Statistics & Insights](#statistics--insights)
5. [Alerts & Anomalies](#alerts--anomalies)
6. [Configuration](#configuration)
7. [Data Sources](#data-sources)

---

## Health & Status

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-16T18:00:00Z",
  "checks": {
    "database": "healthy",
    "ollama": "healthy",
    "task_manager": "healthy",
    "workflow_automation": "healthy"
  }
}
```

### GET /ready

Readiness check endpoint.

**Response:**
```json
{
  "ready": true,
  "services": {
    "api": true,
    "report_generator": true,
    "data_collector": true,
    "llm": true
  }
}
```

### GET /metrics

Prometheus metrics endpoint.

**Response:**
```
# HELP reports_generated_total Total number of reports generated
# TYPE reports_generated_total counter
reports_generated_total{type="daily"} 45
reports_generated_total{type="weekly"} 12

# HELP report_generation_duration_seconds Time to generate reports
# TYPE report_generation_duration_seconds histogram
report_generation_duration_seconds_bucket{type="daily",le="5"} 42
report_generation_duration_seconds_bucket{type="daily",le="10"} 45
```

---

## Reports

### GET /reports

List all available reports.

**Query Parameters:**
- `type` (optional): Filter by report type (`daily`, `weekly`)
- `limit` (optional): Number of reports to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Request:**
```bash
curl http://localhost:8080/api/v1/reports?type=daily&limit=10
```

**Response:**
```json
{
  "reports": [
    {
      "id": "daily-2026-02-16",
      "type": "daily",
      "date": "2026-02-16",
      "status": "completed",
      "formats": ["markdown", "json"],
      "size": 15234,
      "created_at": "2026-02-16T09:00:00Z",
      "download_url": "/api/v1/reports/daily-2026-02-16/download"
    },
    {
      "id": "daily-2026-02-15",
      "type": "daily",
      "date": "2026-02-15",
      "status": "completed",
      "formats": ["markdown", "json"],
      "size": 14892,
      "created_at": "2026-02-15T09:00:00Z",
      "download_url": "/api/v1/reports/daily-2026-02-15/download"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

### GET /reports/{report_id}

Get a specific report.

**Query Parameters:**
- `format` (optional): Output format (`markdown`, `json`, `pdf`) - default: `markdown`

**Request:**
```bash
# Get Markdown version
curl http://localhost:8080/api/v1/reports/daily-2026-02-16

# Get JSON version
curl http://localhost:8080/api/v1/reports/daily-2026-02-16?format=json
```

**Response (Markdown):**
```markdown
# Daily Report - February 16, 2026

## Executive Summary
- **Total Tasks**: 25 (5 completed today)
- **Overdue Tasks**: 3 ⚠️
- **Workflows Executed**: 12 (11 successful, 1 failed)
...
```

**Response (JSON):**
```json
{
  "report_id": "daily-2026-02-16",
  "type": "daily",
  "date": "2026-02-16",
  "generated_at": "2026-02-16T09:00:00Z",
  "summary": {
    "total_tasks": 25,
    "completed_tasks": 5,
    "overdue_tasks": 3,
    "workflows_executed": 12,
    "workflows_successful": 11,
    "workflows_failed": 1
  },
  "tasks": {
    "completed": [...],
    "overdue": [...],
    "in_progress": [...]
  },
  "workflows": {
    "successful": [...],
    "failed": [...]
  },
  "insights": {
    "ai_summary": "The team is making good progress...",
    "recommendations": [...]
  },
  "alerts": [...]
}
```

### GET /reports/{report_id}/download

Download a report file.

**Query Parameters:**
- `format` (optional): File format (`markdown`, `json`, `pdf`) - default: `markdown`

**Request:**
```bash
curl http://localhost:8080/api/v1/reports/daily-2026-02-16/download \
  -o daily-report.md
```

**Response:**
- File download with appropriate Content-Type and Content-Disposition headers

### GET /reports/daily/latest

Get the latest daily report.

**Query Parameters:**
- `format` (optional): Output format - default: `markdown`

**Request:**
```bash
curl http://localhost:8080/api/v1/reports/daily/latest
```

### GET /reports/weekly/latest

Get the latest weekly report.

**Query Parameters:**
- `format` (optional): Output format - default: `markdown`

**Request:**
```bash
curl http://localhost:8080/api/v1/reports/weekly/latest?format=json
```

### DELETE /reports/{report_id}

Delete a specific report.

**Request:**
```bash
curl -X DELETE http://localhost:8080/api/v1/reports/daily-2026-02-10
```

**Response:**
```json
{
  "message": "Report deleted successfully",
  "report_id": "daily-2026-02-10"
}
```

---

## Report Generation

### POST /reports/daily/generate

Generate a new daily report.

**Request Body:**
```json
{
  "date": "2026-02-16",
  "sources": ["task-manager", "workflow-automation"],
  "include_ai_insights": true,
  "include_charts": true,
  "export_formats": ["markdown", "json"]
}
```

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/reports/daily/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["task-manager", "workflow-automation"],
    "include_ai_insights": true
  }'
```

**Response:**
```json
{
  "report_id": "daily-2026-02-16",
  "status": "generated",
  "type": "daily",
  "date": "2026-02-16",
  "formats": ["markdown", "json"],
  "generated_at": "2026-02-16T09:15:23Z",
  "duration_seconds": 12.5,
  "download_url": "/api/v1/reports/daily-2026-02-16/download"
}
```

### POST /reports/weekly/generate

Generate a new weekly report.

**Request Body:**
```json
{
  "week_number": 7,
  "year": 2026,
  "sources": ["task-manager", "workflow-automation"],
  "include_ai_insights": true,
  "include_charts": true,
  "include_trends": true,
  "export_formats": ["markdown", "json"]
}
```

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/reports/weekly/generate \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 7,
    "year": 2026,
    "include_trends": true
  }'
```

**Response:**
```json
{
  "report_id": "weekly-2026-w07",
  "status": "generated",
  "type": "weekly",
  "week_number": 7,
  "year": 2026,
  "date_range": {
    "start": "2026-02-09",
    "end": "2026-02-15"
  },
  "formats": ["markdown", "json"],
  "generated_at": "2026-02-16T09:20:15Z",
  "duration_seconds": 25.3,
  "download_url": "/api/v1/reports/weekly-2026-w07/download"
}
```

### POST /reports/generate

Generate a custom report with a template.

**Request Body:**
```json
{
  "template": "custom-template",
  "title": "Monthly Performance Report",
  "date_range": {
    "start": "2026-02-01",
    "end": "2026-02-28"
  },
  "sources": ["task-manager", "workflow-automation"],
  "parameters": {
    "team": "Engineering",
    "project": "AI Employees"
  },
  "include_ai_insights": true,
  "export_formats": ["markdown", "json", "pdf"]
}
```

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d @custom-report-request.json
```

**Response:**
```json
{
  "report_id": "custom-2026-02-monthly",
  "status": "generated",
  "type": "custom",
  "title": "Monthly Performance Report",
  "formats": ["markdown", "json", "pdf"],
  "generated_at": "2026-02-16T10:00:00Z",
  "duration_seconds": 35.7,
  "download_url": "/api/v1/reports/custom-2026-02-monthly/download"
}
```

### GET /reports/status

Get the status of all report generation jobs.

**Response:**
```json
{
  "active_jobs": 1,
  "queued_jobs": 2,
  "jobs": [
    {
      "job_id": "job-123",
      "report_type": "daily",
      "status": "in_progress",
      "progress": 75,
      "started_at": "2026-02-16T09:00:00Z",
      "estimated_completion": "2026-02-16T09:05:00Z"
    },
    {
      "job_id": "job-124",
      "report_type": "weekly",
      "status": "queued",
      "queued_at": "2026-02-16T09:02:00Z"
    }
  ]
}
```

---

## Statistics & Insights

### GET /reports/stats

Get overall reporting statistics.

**Request:**
```bash
curl http://localhost:8080/api/v1/reports/stats
```

**Response:**
```json
{
  "total_reports": 57,
  "reports_by_type": {
    "daily": 45,
    "weekly": 12
  },
  "last_generated": "2026-02-16T09:00:00Z",
  "next_scheduled": {
    "daily": "2026-02-17T09:00:00Z",
    "weekly": "2026-02-23T09:00:00Z"
  },
  "average_generation_time": 15.2,
  "storage_used": "156MB"
}
```

### GET /reports/stats/tasks

Get task-related statistics from latest report.

**Response:**
```json
{
  "date": "2026-02-16",
  "total_tasks": 25,
  "completed_tasks": 5,
  "in_progress_tasks": 17,
  "overdue_tasks": 3,
  "completion_rate": 0.20,
  "average_completion_time_hours": 18.5,
  "tasks_by_priority": {
    "high": 8,
    "medium": 12,
    "low": 5
  },
  "trend": {
    "completion_rate_change": "+5%",
    "overdue_change": "+2"
  }
}
```

### GET /reports/stats/workflows

Get workflow-related statistics from latest report.

**Response:**
```json
{
  "date": "2026-02-16",
  "total_executions": 12,
  "successful_executions": 11,
  "failed_executions": 1,
  "success_rate": 0.917,
  "average_duration_seconds": 45.2,
  "executions_by_workflow": {
    "data-backup-workflow": 4,
    "example-workflow": 7,
    "notification-workflow": 1
  },
  "trend": {
    "execution_count_change": "+3",
    "success_rate_change": "-8%"
  }
}
```

### GET /reports/insights/tasks

Get AI-generated insights about tasks.

**Response:**
```json
{
  "insights": [
    {
      "type": "progress",
      "severity": "info",
      "message": "The team is making good progress with 20% daily task completion rate.",
      "confidence": 0.95
    },
    {
      "type": "warning",
      "severity": "warning",
      "message": "3 tasks are overdue and may impact project deadlines.",
      "confidence": 0.88,
      "affected_tasks": ["TASK-123", "TASK-124", "TASK-125"]
    }
  ],
  "recommendations": [
    "Consider prioritizing overdue tasks to prevent further delays",
    "The high-priority task backlog is growing - review resource allocation"
  ],
  "generated_at": "2026-02-16T09:00:00Z"
}
```

### GET /reports/insights/workflows

Get AI-generated insights about workflows.

**Response:**
```json
{
  "insights": [
    {
      "type": "performance",
      "severity": "info",
      "message": "Workflow execution success rate is 91.7%, within acceptable range.",
      "confidence": 0.92
    },
    {
      "type": "failure",
      "severity": "error",
      "message": "data-backup-workflow failed due to insufficient disk space.",
      "confidence": 0.99,
      "affected_workflow": "data-backup-workflow"
    }
  ],
  "recommendations": [
    "Monitor disk space to prevent backup failures",
    "Consider implementing disk cleanup automation"
  ],
  "generated_at": "2026-02-16T09:00:00Z"
}
```

### GET /reports/trends

Get trend analysis over time.

**Query Parameters:**
- `period` (optional): Time period (`7d`, `30d`, `90d`) - default: `30d`
- `metrics` (optional): Metrics to include (comma-separated)

**Request:**
```bash
curl http://localhost:8080/api/v1/reports/trends?period=30d
```

**Response:**
```json
{
  "period": "30d",
  "start_date": "2026-01-17",
  "end_date": "2026-02-16",
  "trends": {
    "task_completion_rate": {
      "current": 0.20,
      "average": 0.18,
      "trend": "improving",
      "change_percentage": 11.1
    },
    "workflow_success_rate": {
      "current": 0.917,
      "average": 0.945,
      "trend": "declining",
      "change_percentage": -2.9
    },
    "overdue_tasks": {
      "current": 3,
      "average": 2.1,
      "trend": "worsening",
      "change_count": 0.9
    }
  },
  "data_points": [...]
}
```

---

## Alerts & Anomalies

### GET /alerts

Get current active alerts.

**Query Parameters:**
- `severity` (optional): Filter by severity (`info`, `warning`, `error`, `critical`)
- `limit` (optional): Number of alerts to return

**Request:**
```bash
curl http://localhost:8080/api/v1/alerts?severity=error
```

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "alert-001",
      "type": "workflow_failure",
      "severity": "error",
      "title": "Workflow Execution Failed",
      "message": "data-backup-workflow failed: Insufficient disk space",
      "affected_resource": "data-backup-workflow",
      "created_at": "2026-02-16T08:45:00Z",
      "status": "active",
      "actions": [
        "Free up disk space",
        "Check backup configuration"
      ]
    },
    {
      "alert_id": "alert-002",
      "type": "overdue_tasks",
      "severity": "warning",
      "title": "Overdue Tasks Detected",
      "message": "3 tasks are overdue",
      "affected_tasks": ["TASK-123", "TASK-124", "TASK-125"],
      "created_at": "2026-02-16T09:00:00Z",
      "status": "active"
    }
  ],
  "total": 2
}
```

### GET /alerts/{alert_id}

Get details of a specific alert.

**Response:**
```json
{
  "alert_id": "alert-001",
  "type": "workflow_failure",
  "severity": "error",
  "title": "Workflow Execution Failed",
  "message": "data-backup-workflow failed: Insufficient disk space",
  "affected_resource": "data-backup-workflow",
  "details": {
    "workflow_id": "data-backup-workflow",
    "execution_id": "exec-456",
    "error_message": "No space left on device",
    "timestamp": "2026-02-16T08:45:00Z"
  },
  "created_at": "2026-02-16T08:45:00Z",
  "status": "active",
  "actions": [
    "Free up disk space",
    "Check backup configuration"
  ]
}
```

### POST /alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/alerts/alert-001/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "admin", "note": "Working on disk cleanup"}'
```

**Response:**
```json
{
  "alert_id": "alert-001",
  "status": "acknowledged",
  "acknowledged_by": "admin",
  "acknowledged_at": "2026-02-16T10:00:00Z",
  "note": "Working on disk cleanup"
}
```

### POST /alerts/{alert_id}/resolve

Resolve an alert.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/alerts/alert-001/resolve \
  -H "Content-Type: application/json" \
  -d '{"resolved_by": "admin", "resolution": "Freed up 50GB of disk space"}'
```

**Response:**
```json
{
  "alert_id": "alert-001",
  "status": "resolved",
  "resolved_by": "admin",
  "resolved_at": "2026-02-16T11:00:00Z",
  "resolution": "Freed up 50GB of disk space"
}
```

### GET /alerts/anomalies

Get detected anomalies from AI analysis.

**Response:**
```json
{
  "anomalies": [
    {
      "anomaly_id": "anom-001",
      "type": "task_completion_spike",
      "severity": "info",
      "description": "Task completion rate is 50% higher than usual",
      "detected_at": "2026-02-16T12:00:00Z",
      "confidence": 0.85,
      "baseline_value": 0.18,
      "current_value": 0.27
    },
    {
      "anomaly_id": "anom-002",
      "type": "workflow_failure_rate",
      "severity": "warning",
      "description": "Workflow failure rate increased by 300%",
      "detected_at": "2026-02-16T09:00:00Z",
      "confidence": 0.92,
      "baseline_value": 0.03,
      "current_value": 0.12
    }
  ],
  "total": 2
}
```

### GET /alerts/history

Get alert history.

**Query Parameters:**
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)
- `limit` (optional): Number of records

**Response:**
```json
{
  "history": [
    {
      "alert_id": "alert-003",
      "type": "overdue_tasks",
      "severity": "warning",
      "created_at": "2026-02-15T09:00:00Z",
      "resolved_at": "2026-02-15T14:30:00Z",
      "duration_hours": 5.5,
      "status": "resolved"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

---

## Configuration

### GET /config

Get current configuration.

**Response:**
```json
{
  "reporting": {
    "daily_schedule": "0 9 * * *",
    "weekly_schedule": "0 9 * * 1",
    "default_export_formats": ["markdown", "json"],
    "retention_days": 90
  },
  "integration": {
    "task_manager": {
      "enabled": true,
      "url": "http://task-manager:8080"
    },
    "workflow_automation": {
      "enabled": true,
      "url": "http://workflow-automation:8080"
    }
  },
  "alerts": {
    "enabled": true,
    "thresholds": {
      "overdue_tasks": 5,
      "failed_workflows": 3
    }
  },
  "llm": {
    "provider": "ollama",
    "model": "llama2",
    "temperature": 0.7
  }
}
```

### PATCH /config

Update configuration.

**Request:**
```bash
curl -X PATCH http://localhost:8080/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": {
      "thresholds": {
        "overdue_tasks": 3
      }
    }
  }'
```

**Response:**
```json
{
  "message": "Configuration updated successfully",
  "updated_fields": ["alerts.thresholds.overdue_tasks"]
}
```

---

## Data Sources

### GET /sources

List all configured data sources.

**Response:**
```json
{
  "sources": [
    {
      "id": "task-manager",
      "name": "Task Manager",
      "type": "api",
      "url": "http://task-manager:8080",
      "status": "healthy",
      "last_sync": "2026-02-16T08:55:00Z"
    },
    {
      "id": "workflow-automation",
      "name": "Workflow Automation",
      "type": "api",
      "url": "http://workflow-automation:8080",
      "status": "healthy",
      "last_sync": "2026-02-16T08:55:00Z"
    }
  ]
}
```

### GET /sources/{source_id}/test

Test connectivity to a data source.

**Request:**
```bash
curl http://localhost:8080/api/v1/sources/task-manager/test
```

**Response:**
```json
{
  "source_id": "task-manager",
  "status": "healthy",
  "latency_ms": 45,
  "last_successful_request": "2026-02-16T09:00:00Z",
  "error": null
}
```

### POST /sources/{source_id}/sync

Manually trigger data synchronization.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/sources/task-manager/sync
```

**Response:**
```json
{
  "source_id": "task-manager",
  "sync_status": "completed",
  "records_synced": 25,
  "duration_seconds": 2.3,
  "synced_at": "2026-02-16T09:05:00Z"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "bad_request",
  "message": "Invalid request parameters",
  "details": {
    "field": "date",
    "issue": "Date must be in ISO 8601 format"
  }
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Report not found",
  "report_id": "daily-2026-02-99"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req-12345"
}
```

### 503 Service Unavailable
```json
{
  "error": "service_unavailable",
  "message": "LLM service is temporarily unavailable",
  "retry_after": 60
}
```

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Anonymous**: 100 requests per hour
- **Authenticated**: 1000 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1645012800
```

---

## Webhooks

Configure webhooks to receive notifications when reports are generated or alerts are triggered.

### POST /webhooks

Register a webhook.

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["report.generated", "alert.created"],
    "secret": "webhook-secret"
  }'
```

**Response:**
```json
{
  "webhook_id": "wh-001",
  "url": "https://example.com/webhook",
  "events": ["report.generated", "alert.created"],
  "created_at": "2026-02-16T10:00:00Z",
  "status": "active"
}
```

---

## Complete Example Workflow

```bash
# 1. Check health
curl http://localhost:8080/health

# 2. Generate daily report
REPORT_ID=$(curl -X POST http://localhost:8080/api/v1/reports/daily/generate | jq -r '.report_id')

# 3. Get report in Markdown
curl http://localhost:8080/api/v1/reports/$REPORT_ID

# 4. Download JSON version
curl http://localhost:8080/api/v1/reports/$REPORT_ID/download?format=json \
  -o report.json

# 5. Check for alerts
curl http://localhost:8080/api/v1/alerts

# 6. Get AI insights
curl http://localhost:8080/api/v1/reports/insights/tasks

# 7. View trends
curl http://localhost:8080/api/v1/reports/trends?period=30d
```

---

For more information, see:
- [README.md](README.md) - Architecture overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [INTEGRATION.md](INTEGRATION.md) - Integration guide
