# 🚀 AI Employee Hackathon 2026 — Quick Start Guide

> Get the project running on your laptop in under 10 minutes.

---

## 🖥️ What You Need (Install These First)

| Tool | Purpose | Download |
|------|---------|----------|
| **Docker Desktop** | Run containers | https://www.docker.com/products/docker-desktop |
| **Kind** | Local Kubernetes cluster | https://kind.sigs.k8s.io/docs/user/quick-start/#installation |
| **kubectl** | Control Kubernetes | https://kubernetes.io/docs/tasks/tools/ |
| **Helm** | Deploy Helm charts | https://helm.sh/docs/intro/install/ |
| **Git** | Clone the repo | https://git-scm.com/downloads |

> ✅ Make sure Docker Desktop is **running** before you start.

---

## 📥 Step 1 — Clone the Repo

```powershell
git clone https://github.com/YOUR_USERNAME/AI-Employee-Hackathon-2026.git
cd AI-Employee-Hackathon-2026
```

---

## 🐳 Step 2 — Build Docker Images

```powershell
docker build -t task-manager:latest       -f ./Phase2-Code/task-manager/Dockerfile.slim       ./Phase2-Code/task-manager
docker build -t workflow-automation:latest -f ./Phase2-Code/workflow-automation/Dockerfile.slim ./Phase2-Code/workflow-automation
docker build -t reporting-agent:latest    -f ./Phase2-Code/reporting-agent/Dockerfile.slim    ./Phase2-Code/reporting-agent
docker build -t landing-page:latest       ./Phase2-Code/landing-page
```

---

## ☸️ Step 3 — Create Kubernetes Cluster

```powershell
kind create cluster --name ai-employee
```

---

## 📦 Step 4 — Load Images into Cluster

```powershell
kind load docker-image task-manager:latest       --name ai-employee
kind load docker-image workflow-automation:latest --name ai-employee
kind load docker-image reporting-agent:latest     --name ai-employee
kind load docker-image landing-page:latest        --name ai-employee
```

---

## 🚀 Step 5 — Deploy Everything

```powershell
# Deploy all 3 AI Employees via Helm
.\deploy-all.ps1

# Deploy Phase 5 (HPA, Ingress, ConfigMaps, Prometheus, Grafana)
cd Phase5-CloudNative
.\deploy-phase5.ps1
cd ..
```

---

## 🌐 Step 6 — Start Port Forwards & Open Browser

```powershell
.\port-forward.ps1
```

Then open these URLs in your browser:

| URL | What You See |
|-----|-------------|
| http://localhost:8080 | 🏠 Landing Page — links to all services |
| http://localhost:8081 | 🤖 Task Manager API |
| http://localhost:8081/docs | 📖 Task Manager Swagger Docs |
| http://localhost:8081/demo/tasks | 📋 Sample Tasks JSON |
| http://localhost:8082 | ⚙️ Workflow Automation API |
| http://localhost:8082/docs | 📖 Workflow Swagger Docs |
| http://localhost:8082/demo/workflows | 🔄 Sample Workflows JSON |
| http://localhost:8083 | 📊 Reporting Agent API |
| http://localhost:8083/docs | 📖 Reporting Swagger Docs |
| http://localhost:8083/demo/daily | 📅 Daily Report JSON |
| http://localhost:8083/demo/weekly | 📆 Weekly Report JSON |
| http://localhost:8083/demo/alerts | 🚨 Alerts JSON |
| http://localhost:9090 | 🔥 Prometheus Metrics |
| http://localhost:3000 | 📈 Grafana Dashboard (admin / hackathon123) |

---

## 🛑 Stop Everything

```powershell
# Stop port-forwards
Get-Process kubectl | Stop-Process -Force

# Delete Kind cluster (removes all Kubernetes resources)
kind delete cluster --name ai-employee
```

---

## ❓ Trouble?

| Problem | Fix |
|---------|-----|
| Port-forward drops | Re-run `.\port-forward.ps1` |
| Image not found in cluster | Re-run `kind load docker-image ...` step |
| Pod not starting | Run `kubectl get pods -n default` to check status |
| Grafana not loading | Wait 2 min after deploy, then retry |

---

> 📖 For full project explanation, see **PROJECT-GUIDE.md**
> 🎬 For judge demo commands, see **DEMO-SCRIPT.md**
