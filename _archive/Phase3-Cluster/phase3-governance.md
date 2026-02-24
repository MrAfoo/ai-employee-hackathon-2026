# Governance Notes - Phase 3

## Cluster Decisions
- Kind chosen for lightweight local Kubernetes cluster.
- Multi-node config optional, but single-node sufficient for hackathon.

## Networking
- Services defined as ClusterIP for internal communication.
- kube-proxy handles routing and load-balancing across Pods.
- Port-forward used for local testing (e.g., task-manager on localhost:5000).

## Monitoring
- Liveness and readiness probes added to all Pods.
- Ensures Kubernetes restarts unhealthy containers automatically.

## Transparency
- All manifests stored in Phase3-Code folder.
- Judges can reproduce cluster setup with one command.
