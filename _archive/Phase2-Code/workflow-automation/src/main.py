from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Workflow Automation AI Employee",
    description="Autonomous workflow orchestration that monitors triggers and executes predefined workflows.",
    version="1.0.0"
)

# --- Models ---
class WorkflowStep(BaseModel):
    step: int
    name: str
    status: str
    duration_ms: int
    output: str

class Workflow(BaseModel):
    id: str
    name: str
    trigger: str
    status: str
    steps: List[WorkflowStep]
    started_at: str
    completed_at: Optional[str]
    success: Optional[bool]

class TriggerWorkflow(BaseModel):
    workflow_id: str
    parameters: Optional[dict] = {}

# --- Sample Data ---
SAMPLE_WORKFLOWS: List[Workflow] = [
    Workflow(
        id="wf-001",
        name="Daily Data Backup",
        trigger="schedule:0 2 * * *",
        status="completed",
        steps=[
            WorkflowStep(step=1, name="Validate disk space", status="success", duration_ms=120, output="Available: 45GB"),
            WorkflowStep(step=2, name="Create backup archive", status="success", duration_ms=3200, output="backup_2026-02-15.tar.gz (2.1GB)"),
            WorkflowStep(step=3, name="Verify integrity", status="success", duration_ms=450, output="MD5 checksum verified ✅"),
            WorkflowStep(step=4, name="Cleanup old backups", status="success", duration_ms=90, output="Removed 3 backups older than 30 days"),
        ],
        started_at="2026-02-15T02:00:00",
        completed_at="2026-02-15T02:04:12",
        success=True
    ),
    Workflow(
        id="wf-002",
        name="Task Overdue Alert",
        trigger="event:task.overdue",
        status="completed",
        steps=[
            WorkflowStep(step=1, name="Fetch overdue tasks", status="success", duration_ms=85, output="Found 1 overdue task"),
            WorkflowStep(step=2, name="Generate alert message", status="success", duration_ms=210, output="Alert: 'Setup CI/CD pipeline' is 2 days overdue"),
            WorkflowStep(step=3, name="Send notification", status="success", duration_ms=340, output="Notification sent to Alice via Slack"),
        ],
        started_at="2026-02-16T09:00:00",
        completed_at="2026-02-16T09:00:01",
        success=True
    ),
    Workflow(
        id="wf-003",
        name="Weekly Report Generation",
        trigger="schedule:0 9 * * MON",
        status="in_progress",
        steps=[
            WorkflowStep(step=1, name="Collect task data", status="success", duration_ms=95, output="Fetched 6 tasks from Task Manager"),
            WorkflowStep(step=2, name="Collect workflow logs", status="success", duration_ms=72, output="Fetched 5 workflow runs"),
            WorkflowStep(step=3, name="Generate report", status="running", duration_ms=0, output="Generating with AI..."),
        ],
        started_at="2026-02-16T09:00:00",
        completed_at=None,
        success=None
    ),
]

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "workflow-automation"}

@app.get("/")
def root():
    return {
        "message": "Workflow Automation AI Employee is running",
        "version": "1.0.0",
        "description": "Autonomous workflow orchestration with event and schedule triggers",
        "endpoints": ["/health", "/workflows", "/demo/workflows", "/demo/logs", "/docs"]
    }

@app.get("/workflows", response_model=List[Workflow])
def get_workflows(status: Optional[str] = None):
    """Get all workflows, optionally filtered by status."""
    workflows = SAMPLE_WORKFLOWS
    if status:
        workflows = [w for w in workflows if w.status == status]
    return workflows

@app.get("/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str):
    """Get a specific workflow by ID."""
    wf = next((w for w in SAMPLE_WORKFLOWS if w.id == workflow_id), None)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return wf

@app.post("/workflows/trigger")
def trigger_workflow(trigger: TriggerWorkflow):
    """Trigger a workflow manually."""
    wf = next((w for w in SAMPLE_WORKFLOWS if w.id == trigger.workflow_id), None)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow {trigger.workflow_id} not found")
    return {
        "message": f"Workflow '{wf.name}' triggered successfully",
        "workflow_id": wf.id,
        "parameters": trigger.parameters,
        "triggered_at": datetime.now().isoformat(),
        "estimated_duration": "~4 seconds"
    }

@app.get("/demo/workflows")
def demo_workflows():
    """Demo endpoint showing all workflows with AI analysis."""
    completed = [w for w in SAMPLE_WORKFLOWS if w.status == "completed"]
    in_progress = [w for w in SAMPLE_WORKFLOWS if w.status == "in_progress"]
    success_rate = round(len([w for w in completed if w.success]) / max(len(completed), 1) * 100, 1)
    return {
        "ai_analysis": "Workflow Automation AI Employee has executed 3 workflows",
        "success_rate_percent": success_rate,
        "completed_workflows": len(completed),
        "in_progress_workflows": len(in_progress),
        "workflows": SAMPLE_WORKFLOWS,
        "next_scheduled": [
            {"workflow": "Daily Data Backup", "next_run": "2026-02-17T02:00:00"},
            {"workflow": "Weekly Report Generation", "next_run": "2026-02-23T09:00:00"},
        ],
        "generated_at": datetime.now().isoformat()
    }

@app.get("/demo/logs")
def demo_logs():
    """Demo endpoint showing workflow execution logs."""
    return {
        "logs": [
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Workflow triggered by schedule"},
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Step 1: Collecting task data from task-manager:8080"},
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Step 1: SUCCESS - Fetched 6 tasks"},
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Step 2: Collecting workflow logs"},
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Step 2: SUCCESS - Fetched 5 workflow runs"},
            {"timestamp": "2026-02-16T09:00:00", "level": "INFO", "workflow": "Weekly Report Generation", "message": "Step 3: Generating AI report..."},
            {"timestamp": "2026-02-15T02:04:12", "level": "INFO", "workflow": "Daily Data Backup", "message": "Workflow completed successfully in 252s"},
            {"timestamp": "2026-02-15T02:00:00", "level": "INFO", "workflow": "Daily Data Backup", "message": "Workflow triggered by schedule cron:0 2 * * *"},
        ],
        "total_log_entries": 8,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

