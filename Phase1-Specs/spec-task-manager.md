# Spec: Task Manager AI Employee

## Purpose
This AI Employee autonomously manages tasks, deadlines, and priorities for a small team.

## Capabilities
- Accepts tasks via CLI or API.
- Prioritizes tasks based on deadlines and importance.
- Provides daily status updates automatically.
- Flags overdue tasks and suggests corrective actions.

## Inputs
- Task descriptions (text).
- Deadlines (date/time).
- Priority levels (low, medium, high).

## Outputs
- Organized task list.
- Daily report in Markdown/JSON.
- Alerts for overdue tasks.

## Constraints
- Must run locally using free/open-source tools.
- Deployment reproducible via Docker + Kind/Minikube + Helm.
- Documentation maintained in Obsidian.

## Success Criteria
- Judges can reproduce the deployment with one command.
- AI Employee demonstrates autonomy in managing tasks.
