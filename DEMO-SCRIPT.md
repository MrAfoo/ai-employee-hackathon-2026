# 🤖 AI Employee Hackathon 2026 — Judge Demo Script

> **One page. All commands. Everything you need to evaluate this project.**

---

## ⚡ Step 1 — Start All Services (1 command)

```powershell
.\port-forward.ps1
```

Wait ~5 seconds, then open your browser. That's it!

---

## 🌐 Step 2 — Open the Dashboard

👉 **http://localhost:8080** — Landing page with links to everything

---

## 🧪 Step 3 — Test Each AI Employee

### 📋 Task Manager (Port 8081)
```powershell
# Home
curl http://localhost:8081/

# Health check
curl http://localhost:8081/health

# See sample tasks with priorities & deadlines
curl http://localhost:8081/demo/tasks

# See task summary report
curl http://localhost:8081/demo/summary

# Interactive API docs (open in browser)
start http://localhost:8081/docs
```

### ⚙️ Workflow Automation (Port 8082)
```powershell
# Home
curl http://localhost:8082/

# Health check
curl http://localhost:8082/health

# See sample workflows with triggers & statuses
curl http://localhost:8082/demo/workflows

# See workflow execution logs
curl http://localhost:8082/demo/logs

# Interactive API docs (open in browser)
start http://localhost:8082/docs
```

### 📊 Reporting Agent (Port 8083)
```powershell
# Home
curl http://localhost:8083/

# Health check
curl http://localhost:8083/health

# Today's AI-generated daily report (JSON)
curl http://localhost:8083/demo/daily

# Daily report in Markdown format
curl http://localhost:8083/demo/daily/markdown

# This week's summary report
curl http://localhost:8083/demo/weekly

# Active alerts & anomalies
curl http://localhost:8083/demo/alerts

# All reports overview
curl http://localhost:8083/demo/reports

# Interactive API docs (open in browser)
start http://localhost:8083/docs
```

---

## 📈 Step 4 — Check Observability

```powershell
# Prometheus metrics (open in browser)
start http://localhost:9090

# Grafana dashboards — login: admin / hackathon123
start http://localhost:3000

# Check all pods are running
kubectl get pods --all-namespaces

# Check auto-scaling (HPA)
kubectl get hpa --all-namespaces

# View live logs from any service
kubectl logs -n default -l app.kubernetes.io/name=task-manager --tail=20
kubectl logs -n default -l app.kubernetes.io/name=workflow-automation --tail=20
kubectl logs -n default -l app.kubernetes.io/name=reporting-agent --tail=20
```

---

## 📊 Step 5 — Grafana Live Metrics 

### How to See Graphs in Grafana:
1. Open **http://localhost:3000** → login: `admin` / `hackathon123`
2. Click **Explore** (compass icon 🧭 on left sidebar)
3. Make sure **Prometheus** is selected as the data source (top dropdown)
4. Paste any query below into the query box
5. Click **Run Query** (blue button, top right) → graphs appear!

### 🔥 Queries:

**① CPU Usage of All 3 AI Employees**
```promql
rate(container_cpu_usage_seconds_total{namespace="default", container=~"task-manager|workflow-automation|reporting-agent"}[5m])
```
> Shows real-time CPU consumption of each AI Employee as a line graph

**② Memory Used by Each AI Employee**
```promql
container_memory_usage_bytes{namespace="default", container=~"task-manager|workflow-automation|reporting-agent"}
```
> Shows how much RAM each service is using right now

**③ Pod Restart Count (Shows Resilience)**
```promql
kube_pod_container_status_restarts_total{namespace="default"}
```
> Shows Kubernetes automatically restarted failed pods

**④ Auto-Scaling Status (HPA)**
```promql
kube_horizontalpodautoscaler_status_current_replicas
```
> Shows current replica count — scales 1→5 under high load

**⑤ Network Traffic (Data In/Out)**
```promql
rate(container_network_receive_bytes_total{namespace="default"}[5m])
```
> Shows live network traffic to your services

### 💡 Pro Tip:
- Switch the view from **Table** → **Graph** using the icons at the top of Explore
- Set time range to **Last 1 hour** (top right) for best visualization
- Each coloured line = one AI Employee service

---

## 🔁 Step 6 — Verify Kubernetes Setup (Optional)

```powershell
# See all namespaces
kubectl get namespaces

# See all running services
kubectl get services --all-namespaces

# See Helm releases
helm list --all-namespaces

# See resource limits on pods
kubectl describe pod -n default -l app.kubernetes.io/name=task-manager | findstr -i "limits\|requests\|cpu\|memory"
```

---

## 🛑 Step 7 — Stop Everything

```powershell
Get-Process kubectl | Stop-Process -Force
```

---

## ✅ Expected Results

| URL                          | Expected Response                                 |
| ---------------------------- | ------------------------------------------------- |
| http://localhost:8080        | 🌐 Landing page dashboard                         |
| http://localhost:8081/health | `{"status":"ok","service":"task-manager"}`        |
| http://localhost:8082/health | `{"status":"ok","service":"workflow-automation"}` |
| http://localhost:8083/health | `{"status":"ok","service":"reporting-agent"}`     |
| http://localhost:9090        | Prometheus metrics UI                             |
| http://localhost:3000        | Grafana dashboard (admin/hackathon123)            |

---

*For full project explanation → see **PROJECT-GUIDE.md***
