# Workflow Automation AI Employee - API Documentation

## Base URL
```
http://localhost:8080
```

## Authentication
Currently, authentication is optional. Set `ENABLE_AUTH=true` and provide `API_KEY` in environment to enable.

When enabled, include the API key in the header:
```
Authorization: Bearer <your-api-key>
```

---

## Endpoints

### Health Check

#### GET /health
Check if the service is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-16T18:30:00Z",
  "version": "1.0.0",
  "services": {
    "redis": "connected",
    "llm": "available"
  }
}
```

---

### Workflow Management

#### GET /workflows
List all available workflow definitions.

**Response:**
```json
{
  "workflows": [
    {
      "name": "example-workflow",
      "description": "Example workflow demonstrating capabilities",
      "version": "1.0",
      "triggers": ["schedule", "event", "webhook"],
      "enabled": true
    },
    {
      "name": "data-backup",
      "description": "Automated data backup workflow",
      "version": "1.0",
      "triggers": ["schedule"],
      "enabled": true
    }
  ]
}
```

#### GET /workflows/{workflow_name}
Get details of a specific workflow.

**Response:**
```json
{
  "name": "example-workflow",
  "description": "Example workflow demonstrating capabilities",
  "version": "1.0",
  "triggers": [
    {
      "type": "schedule",
      "cron": "0 9 * * *",
      "enabled": true
    }
  ],
  "parameters": [
    {
      "name": "input_data",
      "type": "string",
      "required": false,
      "default": "test data"
    }
  ],
  "steps": [...]
}
```

#### POST /workflows/{workflow_name}/trigger
Manually trigger a workflow execution.

**Request Body:**
```json
{
  "parameters": {
    "input_data": "custom data",
    "notification_enabled": true
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "workflow_name": "example-workflow",
  "status": "running",
  "started_at": "2026-02-16T18:30:00Z",
  "parameters": {
    "input_data": "custom data",
    "notification_enabled": true
  }
}
```

---

### Execution Management

#### GET /executions
List workflow executions with optional filtering.

**Query Parameters:**
- `workflow_name` (optional): Filter by workflow name
- `status` (optional): Filter by status (running, completed, failed, timeout)
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "executions": [
    {
      "execution_id": "exec_abc123",
      "workflow_name": "example-workflow",
      "status": "completed",
      "started_at": "2026-02-16T18:30:00Z",
      "completed_at": "2026-02-16T18:31:30Z",
      "duration": "90s"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

#### GET /executions/{execution_id}
Get detailed information about a specific execution.

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "workflow_name": "example-workflow",
  "status": "completed",
  "started_at": "2026-02-16T18:30:00Z",
  "completed_at": "2026-02-16T18:31:30Z",
  "duration": "90s",
  "parameters": {
    "input_data": "custom data"
  },
  "steps": [
    {
      "name": "validate-input",
      "status": "completed",
      "started_at": "2026-02-16T18:30:00Z",
      "completed_at": "2026-02-16T18:30:05Z",
      "duration": "5s",
      "output": "Validation successful"
    }
  ],
  "logs": [
    {
      "timestamp": "2026-02-16T18:30:00Z",
      "level": "info",
      "message": "Starting workflow execution"
    }
  ]
}
```

#### DELETE /executions/{execution_id}
Cancel a running workflow execution.

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "status": "cancelled",
  "message": "Workflow execution cancelled successfully"
}
```

---

### Logs and Monitoring

#### GET /executions/{execution_id}/logs
Get logs for a specific execution.

**Query Parameters:**
- `level` (optional): Filter by log level (debug, info, warning, error)
- `tail` (optional): Return only the last N lines

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "logs": [
    {
      "timestamp": "2026-02-16T18:30:00Z",
      "level": "info",
      "step": "validate-input",
      "message": "Validating input: custom data"
    },
    {
      "timestamp": "2026-02-16T18:30:05Z",
      "level": "info",
      "step": "validate-input",
      "message": "Validation successful"
    }
  ]
}
```

#### GET /metrics
Get Prometheus-format metrics.

**Response:**
```
# HELP workflow_executions_total Total number of workflow executions
# TYPE workflow_executions_total counter
workflow_executions_total{workflow="example-workflow",status="completed"} 42

# HELP workflow_execution_duration_seconds Workflow execution duration
# TYPE workflow_execution_duration_seconds histogram
workflow_execution_duration_seconds_bucket{workflow="example-workflow",le="30"} 10
workflow_execution_duration_seconds_bucket{workflow="example-workflow",le="60"} 35
```

#### GET /stats
Get workflow execution statistics.

**Response:**
```json
{
  "total_executions": 150,
  "running": 3,
  "completed": 135,
  "failed": 10,
  "cancelled": 2,
  "success_rate": 0.90,
  "average_duration": "75s",
  "workflows": {
    "example-workflow": {
      "executions": 80,
      "success_rate": 0.95,
      "average_duration": "60s"
    },
    "data-backup": {
      "executions": 70,
      "success_rate": 0.85,
      "average_duration": "90s"
    }
  }
}
```

---

## Webhook Triggers

Workflows with webhook triggers can be called via:

#### POST /trigger/{workflow_name}
Trigger a workflow via webhook.

**Request Body:**
```json
{
  "event_data": {
    "source": "external-system",
    "payload": "any data"
  },
  "parameters": {
    "input_data": "webhook triggered data"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_name": "example-workflow",
  "status": "running",
  "message": "Workflow triggered successfully"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "message": "Missing required parameter: workflow_name",
  "code": "BAD_REQUEST"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "message": "Workflow 'invalid-workflow' not found",
  "code": "NOT_FOUND"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Failed to execute workflow",
  "code": "INTERNAL_ERROR"
}
```

---

## CLI Usage

In addition to the REST API, workflows can be triggered via CLI:

```bash
# Trigger a workflow
curl -X POST http://localhost:8080/workflows/example-workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"input_data": "test"}}'

# Check execution status
curl http://localhost:8080/executions/exec_abc123

# View logs
curl http://localhost:8080/executions/exec_abc123/logs
```

---

## Rate Limiting

Currently no rate limiting is implemented. This can be added in production deployments using:
- Kubernetes Ingress rate limiting
- API Gateway
- Application-level rate limiting middleware
