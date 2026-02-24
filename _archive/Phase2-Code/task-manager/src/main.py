from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(
    title="Task Manager AI Employee",
    description="Autonomous task management service that prioritizes and tracks team tasks.",
    version="1.0.0"
)

# --- Models ---
class Task(BaseModel):
    id: int
    title: str
    description: str
    priority: str  # low, medium, high
    status: str    # pending, in_progress, completed, overdue
    deadline: str
    assignee: str
    created_at: str

class CreateTask(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    deadline: str
    assignee: str

# --- Sample Data ---
SAMPLE_TASKS: List[Task] = [
    Task(id=1, title="Design system architecture", description="Define microservices layout and API contracts", priority="high", status="completed", deadline="2026-02-10", assignee="Alice", created_at="2026-02-01"),
    Task(id=2, title="Implement task API endpoints", description="Build CRUD endpoints for task management", priority="high", status="in_progress", deadline="2026-02-18", assignee="Bob", created_at="2026-02-05"),
    Task(id=3, title="Write unit tests", description="Cover all service endpoints with pytest", priority="medium", status="pending", deadline="2026-02-20", assignee="Charlie", created_at="2026-02-08"),
    Task(id=4, title="Setup CI/CD pipeline", description="Configure GitHub Actions for automated builds", priority="medium", status="overdue", deadline="2026-02-14", assignee="Alice", created_at="2026-02-03"),
    Task(id=5, title="Documentation review", description="Review and update all README and API docs", priority="low", status="pending", deadline="2026-02-25", assignee="Bob", created_at="2026-02-10"),
    Task(id=6, title="Deploy to Kubernetes", description="Helm chart deployment to Kind cluster", priority="high", status="in_progress", deadline="2026-02-16", assignee="Charlie", created_at="2026-02-12"),
]

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "task-manager"}

@app.get("/")
def root():
    return {
        "message": "Task Manager AI Employee is running",
        "version": "1.0.0",
        "description": "Autonomous task management with priority-based scheduling",
        "endpoints": ["/health", "/tasks", "/demo/tasks", "/demo/summary", "/docs"]
    }

@app.get("/tasks", response_model=List[Task])
def get_tasks(priority: Optional[str] = None, status: Optional[str] = None):
    """Get all tasks, optionally filtered by priority or status."""
    tasks = SAMPLE_TASKS
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if status:
        tasks = [t for t in tasks if t.status == status]
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    """Get a specific task by ID."""
    task = next((t for t in SAMPLE_TASKS if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.post("/tasks", response_model=Task)
def create_task(task: CreateTask):
    """Create a new task."""
    new_id = max(t.id for t in SAMPLE_TASKS) + 1
    new_task = Task(
        id=new_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status="pending",
        deadline=task.deadline,
        assignee=task.assignee,
        created_at=datetime.now().strftime("%Y-%m-%d")
    )
    SAMPLE_TASKS.append(new_task)
    return new_task

@app.get("/demo/tasks")
def demo_tasks():
    """Demo endpoint showing sample tasks with AI prioritization."""
    overdue = [t for t in SAMPLE_TASKS if t.status == "overdue"]
    high_priority = [t for t in SAMPLE_TASKS if t.priority == "high" and t.status != "completed"]
    return {
        "ai_analysis": "Task Manager AI Employee has analyzed 6 tasks",
        "alerts": [f"⚠️ OVERDUE: '{t.title}' assigned to {t.assignee}" for t in overdue],
        "high_priority_queue": [{"id": t.id, "title": t.title, "assignee": t.assignee, "deadline": t.deadline} for t in high_priority],
        "all_tasks": SAMPLE_TASKS,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/demo/summary")
def demo_summary():
    """Demo endpoint showing task statistics and AI insights."""
    total = len(SAMPLE_TASKS)
    completed = len([t for t in SAMPLE_TASKS if t.status == "completed"])
    overdue = len([t for t in SAMPLE_TASKS if t.status == "overdue"])
    in_progress = len([t for t in SAMPLE_TASKS if t.status == "in_progress"])
    pending = len([t for t in SAMPLE_TASKS if t.status == "pending"])
    completion_rate = round((completed / total) * 100, 1)
    return {
        "summary": {
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "overdue": overdue,
            "completion_rate_percent": completion_rate
        },
        "ai_insights": [
            f"Completion rate is {completion_rate}% - {'on track ✅' if completion_rate >= 50 else 'needs attention ⚠️'}",
            f"{overdue} task(s) are overdue and require immediate attention",
            f"{in_progress} task(s) currently in progress"
        ],
        "recommended_actions": [
            "Reassign overdue tasks immediately",
            "Daily standup to unblock in-progress tasks",
            "Review low priority tasks for deferral"
        ],
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

