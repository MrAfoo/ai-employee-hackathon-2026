# Phase 5 Index - Cloud Native Features

## Overview
Phase 5 introduces advanced cloud-native features including horizontal pod autoscaling, ingress routing, configuration management, and comprehensive observability.

---

## Directory Structure

```
Phase5-CloudNative/
├── hpa/                              # Horizontal Pod Autoscalers
│   ├── task-manager-hpa.yaml
│   ├── workflow-automation-hpa.yaml
│   └── reporting-agent-hpa.yaml
│
├── ingress/                          # Ingress Configuration
│   └── ingress.yaml
│
├── config/                           # Configuration Management
│   ├── configmaps.yaml
│   └── secrets.yaml
│
├── observability/                    # Monitoring & Logging
│   ├── monitoring.yaml
│   ├── check-health.ps1
│   ├── view-logs.ps1
│   └── metrics-dashboard.ps1
│
├── deploy-phase5.ps1                 # Main deployment script
├── undeploy-phase5.ps1               # Cleanup script
├── install-nginx-ingress.ps1         # NGINX ingress installer
├── test-ingress.ps1                  # Ingress testing script
│
├── README.md                         # This file
├── QUICKSTART.md                     # Quick start guide
├── Phase5-Index.md                   # Component index
└── Phase5-Governance.md              # Governance decisions
```

---

## Components

### 1. Horizontal Pod Autoscalers (HPA)

**Location:** `hpa/`

| Service | Min Replicas | Max Replicas | Target CPU | Target Memory |
|---------|--------------|--------------|------------|---------------|
| Task Manager | 1 | 5 | 80% | 80% |
| Workflow Automation | 1 | 5 | 80% | 80% |
| Reporting Agent | 1 | 5 | 80% | 80% |

**Features:**
- CPU-based autoscaling
- Memory-based autoscaling
- Scale-down stabilization (5 minutes)
- Scale-up stabilization (instant)
- Gradual scale-down (50% per 15s)
- Aggressive scale-up (100% or 2 pods per 15s)

**Deploy:**
```powershell
kubectl apply -f hpa/
```

**Verify:**
```powershell
kubectl get hpa --all-namespaces
```

---

### 2. Ingress Controller

**Location:** `ingress/`

**Features:**
- NGINX Ingress Controller
- Path-based routing
- All services accessible via localhost
- TLS/SSL ready
- Rate limiting support

**Routes:**
- `/reporting` → Reporting Agent (namespace: reporting)
- `/task` → Task Manager (namespace: task-manager)
- `/workflow` → Workflow Automation (namespace: workflow)

**Install NGINX Ingress:**
```powershell
.\install-nginx-ingress.ps1
```

**Deploy Ingress Rules:**
```powershell
kubectl apply -f ingress/ingress.yaml
```

**Test Ingress:**
```powershell
.\test-ingress.ps1
```

**Access Services:**
```bash
curl http://localhost/reporting/health
curl http://localhost/task/health
curl http://localhost/workflow/health
```

---

### 3. Configuration Management

**Location:** `config/`

#### ConfigMaps
- **app-config:** Application environment settings
- **task-manager-config:** Task manager specific config
- **workflow-automation-config:** Workflow specific config
- **reporting-agent-config:** Reporting specific config

**Environments Supported:**
- Production
- Development
- Testing

#### Secrets
- **db-secret:** Database credentials
- **api-keys:** External API keys
- **llm-config:** LLM service credentials
- **tls-certs:** TLS certificates

**Deploy:**
```powershell
kubectl apply -f config/
```

**View ConfigMaps:**
```powershell
kubectl get configmaps --all-namespaces
```

**View Secrets:**
```powershell
kubectl get secrets --all-namespaces
```

---

### 4. Observability

**Location:** `observability/`

#### Monitoring
- **ServiceMonitor:** Prometheus integration
- **Metrics endpoints:** All services expose `/metrics`
- **Scrape interval:** 30 seconds

#### Health Checks
```powershell
.\observability\check-health.ps1
```

**What it checks:**
- Pod status (all namespaces)
- Service endpoints
- Health endpoint responses
- Resource usage
- HPA status

#### Log Viewing
```powershell
.\observability\view-logs.ps1
```

**Options:**
- View logs by namespace
- View logs by service
- Follow logs in real-time
- Filter by time range

#### Metrics Dashboard
```powershell
.\observability\metrics-dashboard.ps1
```

**Metrics Available:**
- CPU usage per pod
- Memory usage per pod
- Request count
- Response times
- Error rates
- HPA scaling events

---

## Deployment Scripts

### Main Deployment
```powershell
.\deploy-phase5.ps1
```

**What it does:**
1. Installs NGINX Ingress Controller
2. Applies all HPAs
3. Creates ConfigMaps and Secrets
4. Deploys Ingress rules
5. Sets up monitoring
6. Verifies deployment

### Cleanup
```powershell
.\undeploy-phase5.ps1
```

**What it does:**
1. Removes all HPAs
2. Deletes Ingress rules
3. Removes ConfigMaps and Secrets
4. Cleans up monitoring resources
5. Optionally removes NGINX Ingress Controller

---

## Namespaces Used

| Namespace | Purpose | Services |
|-----------|---------|----------|
| `reporting` | Reporting Agent | reporting-agent |
| `task-manager` | Task Management | task-manager |
| `workflow` | Workflow Automation | workflow-automation |
| `ingress-nginx` | Ingress Controller | nginx-ingress-controller |

---

## Prerequisites

### Required
- Kubernetes cluster (Kind/Minikube)
- kubectl configured
- Helm 3.x (optional)
- PowerShell 5.1+ or PowerShell Core 7+

### Optional
- Prometheus
- Grafana
- Metrics Server (for HPA)

### Install Metrics Server (Required for HPA)
```powershell
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

For Kind/Minikube, patch metrics-server:
```powershell
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

---

## Quick Commands Reference

### HPA Management
```powershell
# View all HPAs
kubectl get hpa --all-namespaces

# Describe HPA
kubectl describe hpa task-manager-hpa -n task-manager

# Edit HPA
kubectl edit hpa reporting-agent-hpa -n reporting

# Delete HPA
kubectl delete hpa workflow-automation-hpa -n workflow
```

### Ingress Management
```powershell
# View Ingress rules
kubectl get ingress --all-namespaces

# Describe Ingress
kubectl describe ingress hackathon-ingress

# View NGINX controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Test Ingress
curl http://localhost/reporting/health
```

### Config & Secrets Management
```powershell
# View ConfigMaps
kubectl get cm --all-namespaces

# View Secret (base64 encoded)
kubectl get secret db-secret -o yaml

# Decode Secret
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 -d

# Update ConfigMap
kubectl edit cm app-config
```

### Monitoring
```powershell
# Check pod metrics
kubectl top pods --all-namespaces

# Check node metrics
kubectl top nodes

# View events
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
```

---

## Troubleshooting

### HPA Not Scaling
```powershell
# Check metrics server is running
kubectl get deployment metrics-server -n kube-system

# Check if metrics are available
kubectl top pods -n reporting

# Check HPA events
kubectl describe hpa reporting-agent-hpa -n reporting
```

### Ingress Not Working
```powershell
# Check NGINX controller
kubectl get pods -n ingress-nginx

# Check Ingress rules
kubectl get ingress

# Check service endpoints
kubectl get endpoints -n reporting

# View NGINX logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### ConfigMap/Secret Issues
```powershell
# Verify ConfigMap exists
kubectl get cm app-config

# Check if pods are using ConfigMap
kubectl describe pod <pod-name> -n <namespace>

# Restart pods to pick up changes
kubectl rollout restart deployment/<deployment-name> -n <namespace>
```

---

## Best Practices

### HPA
1. Set appropriate min/max replicas based on workload
2. Use both CPU and memory metrics
3. Configure scale-down stabilization to prevent flapping
4. Monitor scaling events and adjust thresholds

### Ingress
1. Use path-based routing for better organization
2. Enable rate limiting for production
3. Configure TLS/SSL for security
4. Set appropriate timeouts

### Configuration
1. Use ConfigMaps for non-sensitive configuration
2. Use Secrets for sensitive data (credentials, keys)
3. Enable encryption at rest for Secrets
4. Version control ConfigMaps for rollback capability

### Observability
1. Enable metrics collection on all services
2. Set up centralized logging
3. Create alerts for critical metrics
4. Regular health check monitoring

---

## Integration with Previous Phases

### Phase 4 Integration
- Builds on namespace structure from Phase 4
- Uses resource limits defined in Phase 4
- Extends health probes with autoscaling

### Phase 2 Integration
- Uses Docker images from Phase 2
- References Helm charts from Phase 2
- Extends deployment manifests from Phase 2

---

## Next Steps

1. **Deploy Phase 5:**
   ```powershell
   .\deploy-phase5.ps1
   ```

2. **Verify Deployment:**
   ```powershell
   .\observability\check-health.ps1
   ```

3. **Test Ingress:**
   ```powershell
   .\test-ingress.ps1
   ```

4. **Monitor Metrics:**
   ```powershell
   .\observability\metrics-dashboard.ps1
   ```

5. **View Documentation:**
   - Read `README.md` for overview
   - Check `QUICKSTART.md` for quick start
   - Review `Phase5-Governance.md` for decisions

---

## Resources

### Documentation
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [NGINX Ingress](https://kubernetes.github.io/ingress-nginx/)
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

### Tools
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/)
- [Kind](https://kind.sigs.k8s.io/)
- [Minikube](https://minikube.sigs.k8s.io/)

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review governance documentation
3. Consult Kubernetes documentation
4. Check deployment logs

---

**Last Updated:** 2026-02-16
**Phase:** 5 - Cloud Native Features
**Status:** Complete
