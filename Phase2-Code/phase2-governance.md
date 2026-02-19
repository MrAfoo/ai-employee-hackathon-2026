# Governance Notes - Phase 2

## Tooling Decisions
- Kubernetes via Kind (disk space constraints, avoided Docker Desktop).
- Helm for reproducible installs.
- FastAPI for lightweight services.

## Fixes Applied
- Added reporting.dailyReport.enabled and schedule.
- Added reporting.weeklyReport.enabled and schedule.
- Added anomalyDetection.enabled block.
- Corrected Dockerfile CMD to run src/main.py.

## Reviewability
- Each service has its own folder with Dockerfile, requirements.txt, src/, config/.
- Helm lint passes cleanly for all charts.
- Pods verified running via kubectl get pods.
