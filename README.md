# 🤖 AI Employee Hackathon 2026 — Complete Project Guide

> **For beginners:** This guide explains everything in simple language.  
> No prior experience with Docker or Kubernetes needed to understand this!

---

## 📖 What Is This Project?

Imagine you have **3 robot employees** working for your team — automatically, 24/7, without breaks.  
That's exactly what this project builds!

These **AI Employees** are software programs that:
- 📋 **Manage your tasks** (like a smart to-do list that organizes itself)
- ⚙️ **Run workflows automatically** (like a robot that does repetitive jobs for you)
- 📊 **Write reports for you** (summarizes what happened each day/week)

They run inside **containers** (like small self-contained boxes of software) on a **Kubernetes cluster** (a system that manages and runs those boxes).

---

## 🗺️ Simple Architecture — What's Happening?

```
┌─────────────────────────────────────────────────────────────────────┐
│                     YOUR COMPUTER (localhost)                        │
│                                                                     │
│   🌐 Browser                                                        │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              NGINX Ingress (Traffic Router)                  │   │
│  │   Routes your browser requests to the right AI Employee      │   │
│  └──────────┬──────────────┬──────────────┬────────────────────┘   │
│             │              │              │                         │
│             ▼              ▼              ▼                         │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│    │ 📋 Task      │ │ ⚙️ Workflow  │ │ 📊 Reporting │             │
│    │   Manager   │ │  Automation  │ │    Agent     │             │
│    │  :8081      │ │   :8082      │ │   :8083      │             │
│    └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                     │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│    │ 🌐 Landing  │ │ 📈 Prometheus│ │ 📊 Grafana   │             │
│    │    Page     │ │    :9090     │ │   :3000      │             │
│    │   :8080     │ │  (Metrics)   │ │ (Dashboard)  │             │
│    └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         KIND Kubernetes Cluster (ai-employee)                │   │
│  │   Manages all containers, restarts them if they crash,      │   │
│  │   scales them up/down based on load (HPA)                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### In Plain English:
1. You open your **browser** and visit `localhost:8080`
2. The **Landing Page** shows you links to all 3 AI Employees
3. Each AI Employee is a **FastAPI app** running in a Docker container
4. **Kubernetes** (via Kind) keeps everything running and healthy
5. **Prometheus** collects health data; **Grafana** shows it as charts

---

## 📁 Project Structure — What Each Folder Does

```
AI-Employee-Hackathon-2026/
│
├── 📁 Phase1-Specs/          ← Step 1: The plan (what we want to build)
│   ├── spec-task-manager.md       Plans for Task Manager
│   ├── spec-workflow-automation.md Plans for Workflow Automation
│   └── spec-reporting-agent.md    Plans for Reporting Agent
│
├── 📁 Phase2-Code/           ← Step 2: The actual code & Docker setup
│   ├── 📁 task-manager/          Task Manager AI Employee
│   │   ├── Dockerfile            Recipe to build the container image
│   │   ├── Dockerfile.slim       Lightweight version (faster to build)
│   │   ├── requirements.txt      Python libraries needed
│   │   ├── src/main.py           The actual FastAPI application code
│   │   ├── helm/                 Helm chart (smart Kubernetes installer)
│   │   └── k8s/                  Raw Kubernetes config files
│   │
│   ├── 📁 workflow-automation/   Workflow Automation AI Employee
│   │   ├── Dockerfile            Container recipe
│   │   ├── src/main.py           FastAPI app with workflow demo data
│   │   ├── helm/                 Helm chart
│   │   └── k8s/                  Kubernetes manifests
│   │
│   ├── 📁 reporting-agent/       Reporting Agent AI Employee
│   │   ├── Dockerfile            Container recipe
│   │   ├── src/main.py           FastAPI app with report demo data
│   │   ├── helm/                 Helm chart
│   │   └── k8s/                  Kubernetes manifests
│   │
│   ├── 📁 landing-page/          The web dashboard (http://localhost:8080)
│   │   ├── index.html            The HTML page you see in browser
│   │   ├── Dockerfile            Container recipe using nginx
│   │   └── k8s/deployment.yaml   Kubernetes config
│   │
│   └── 📁 k8s-namespaces/        Kubernetes namespace configs
│
├── 📁 Phase3-Cluster/        ← Step 3: Kubernetes cluster setup notes
│
├── 📁 Phase4-Deployment/     ← Step 4: Deployment scripts
│   ├── deploy-all.ps1            One-command deploy (Windows)
│   └── undeploy-all.ps1          One-command cleanup (Windows)
│
├── 📁 Phase5-CloudNative/    ← Step 5: Advanced cloud features
│   ├── hpa/                      Auto-scaling configs (scale up under load)
│   ├── ingress/                  Traffic routing rules
│   ├── config/                   ConfigMaps & Secrets
│   ├── observability/            Monitoring scripts
│   ├── deploy-phase5.ps1         Deploy Phase 5 features
│   └── undeploy-phase5.ps1       Clean up Phase 5
│
└── port-forward.ps1          ← 🚀 START HERE! Opens all services in browser
```

---

## 🤖 The 3 AI Employees — What They Do

### 1. 📋 Task Manager (Port 8081)
**What it does:** Manages tasks for your team like a smart assistant.

| Feature | Description |
|---------|-------------|
| Create tasks | Add tasks with title, priority, deadline |
| Auto-prioritize | Sorts tasks by urgency (high/medium/low) |
| Flag overdue | Alerts when tasks are past deadline |
| Daily updates | Automatically reports task status |

**Try it:** http://localhost:8081/demo/tasks

---

### 2. ⚙️ Workflow Automation (Port 8082)
**What it does:** Runs repetitive jobs automatically so humans don't have to.

| Feature | Description |
|---------|-------------|
| Monitor triggers | Watches for events (schedule, file change) |
| Run workflows | Executes predefined steps automatically |
| Log everything | Keeps a full record of what it did |
| Send alerts | Notifies you when a workflow succeeds or fails |

**Try it:** http://localhost:8082/demo/workflows

---

### 3. 📊 Reporting Agent (Port 8083)
**What it does:** Automatically writes reports so you don't have to.

| Feature | Description |
|---------|-------------|
| Daily reports | Auto-generates a summary every morning |
| Weekly reports | Bigger summary every Monday |
| Anomaly alerts | Flags anything unusual (overdue tasks, failed workflows) |
| Export formats | Saves reports as Markdown and JSON |

**Try it:**
- http://localhost:8083/demo/daily
- http://localhost:8083/demo/weekly
- http://localhost:8083/demo/alerts

---

## 🛠️ Technologies Used — Explained Simply

| Technology | What It Is | Why We Use It |
|-----------|-----------|---------------|
| **Python** | Programming language | We write AI Employee code in it |
| **FastAPI** | Web framework for Python | Makes our code accessible via web browser |
| **Docker** | Containerization tool | Packages code so it runs anywhere |
| **Kubernetes (K8s)** | Container manager | Runs & manages all our Docker containers |
| **Kind** | Kubernetes on your laptop | Lets us run Kubernetes locally for free |
| **Helm** | Kubernetes package manager | Like an installer for Kubernetes apps |
| **NGINX Ingress** | Traffic router | Sends browser requests to the right service |
| **Prometheus** | Metrics collector | Collects health & performance data |
| **Grafana** | Dashboard tool | Shows metrics as pretty charts |
| **HPA** | Auto-scaler | Adds more containers when traffic is high |

---

## 🔄 How It All Connects — Step by Step

```
STEP 1: You write specs (Phase 1)
         ↓
         "I want an AI that manages tasks"

STEP 2: Code is written (Phase 2)
         ↓
         Python FastAPI apps created for each AI Employee
         Dockerfiles written to package them into containers

STEP 3: Cluster is set up (Phase 3)
         ↓
         Kind creates a local Kubernetes cluster on your laptop
         kubectl apply -f deploys the containers to Kubernetes

STEP 4: Deploy everything (Phase 4)
         ↓
         Helm charts install all 3 AI Employees
         Namespaces separate them cleanly
         Resource limits prevent memory/CPU overuse

STEP 5: Make it cloud-ready (Phase 5)
         ↓
         HPA auto-scales pods when traffic increases
         NGINX Ingress routes traffic to the right service
         Prometheus + Grafana monitor everything
         Secrets & ConfigMaps manage config securely
```

---

## 🚀 How to Run This Project (Beginner-Friendly)

### Prerequisites (What You Need Installed)
- ✅ Docker Desktop
- ✅ Kind (`winget install kind`)
- ✅ kubectl (`winget install kubectl`)
- ✅ Helm (`winget install helm`)

### Step 1: Start Everything
```powershell
# From project root like mine: F:\vs\ai-employee\AI-Employee-Hackathon-2026
.\port-forward.ps1
```
This opens all 6 services in the background.

### Step 2: Open the Landing Page
```
http://localhost:8080
```
You'll see the dashboard with links to everything!

### Step 3: Explore the AI Employees
| Service | URL | What You'll See |
|---------|-----|-----------------|
| 🌐 Dashboard | http://localhost:8080 | Links to all services |
| 📋 Task Manager | http://localhost:8081 | Task management API |
| 📋 Task Docs | http://localhost:8081/docs | Interactive API docs |
| 📋 Task Demo | http://localhost:8081/demo/tasks | Sample tasks JSON |
| ⚙️ Workflow | http://localhost:8082 | Workflow automation API |
| ⚙️ Workflow Docs | http://localhost:8082/docs | Interactive API docs |
| ⚙️ Workflow Demo | http://localhost:8082/demo/workflows | Sample workflows JSON |
| 📊 Reports | http://localhost:8083 | Reporting agent API |
| 📊 Report Docs | http://localhost:8083/docs | Interactive API docs |
| 📊 Daily Report | http://localhost:8083/demo/daily | Today's report JSON |
| 📊 Weekly Report | http://localhost:8083/demo/weekly | This week's report JSON |
| 📊 Alerts | http://localhost:8083/demo/alerts | Active alerts JSON |
| 📈 Prometheus | http://localhost:9090 | Metrics & monitoring |
| 📊 Grafana | http://localhost:3000 | Visual dashboards |

> **Grafana login:** username `admin`, password `hackathon123`

### Step 4: Stop Everything
```powershell
Get-Process kubectl | Stop-Process -Force
```

---

## 📊 What Auto-Scaling Means (HPA Explained Simply)

Imagine your Task Manager gets 1000 users at once.  
One container can't handle that — it would crash!

**HPA (Horizontal Pod Autoscaler)** automatically:
```
Normal load:   [Pod 1]                    ← 1 container running
Medium load:   [Pod 1] [Pod 2]            ← 2 containers running
Heavy load:    [Pod 1] [Pod 2] [Pod 3]    ← 3 containers running
Very heavy:    [Pod 1] [Pod 2] [Pod 3] [Pod 4] [Pod 5]  ← max 5
```

It scales **up** when CPU > 80% and scales **down** when load drops.  
This happens automatically — no human needed! ✅

---

## 🔐 ConfigMaps & Secrets Explained Simply

**ConfigMap** = Public settings (like app configuration)
```yaml
ENV=production
LOG_LEVEL=INFO
```

**Secret** = Private settings (like passwords) — stored encrypted
```yaml
DB_PASSWORD=******* (hidden)
API_KEY=******* (hidden)
```

Think of ConfigMap as a sticky note on your desk,  
and Secret as a note locked in a safe.

---

## 📈 Monitoring Explained Simply

```
Each AI Employee → sends metrics → Prometheus collects them
                                          ↓
                               Grafana reads from Prometheus
                                          ↓
                         You see pretty charts & graphs at :3000
```

**What gets monitored:**
- Is the service alive? ✅ or ❌
- How much CPU is it using?
- How much memory is it using?
- How many requests per second?

---

## 🗂️ Key Files Quick Reference

| File | What It Does |
|------|-------------|
| `port-forward.ps1` | 🚀 Starts all services — run this first! |
| `Phase4-Deployment/deploy-all.ps1` | Deploys everything to Kubernetes |
| `Phase4-Deployment/undeploy-all.ps1` | Removes everything from Kubernetes |
| `Phase5-CloudNative/deploy-phase5.ps1` | Deploys HPA, Ingress, monitoring |
| `Phase2-Code/*/Dockerfile.slim` | Lightweight container recipe for each service |
| `Phase2-Code/*/helm/` | Helm chart for each service |
| `Phase2-Code/*/k8s/` | Raw Kubernetes manifests |
| `Phase2-Code/*/src/main.py` | The actual API code for each service |
| `Phase2-Code/landing-page/index.html` | The web dashboard UI |

---

## ❓ Common Questions

**Q: What is a container?**  
A: Think of it like a lunchbox. It has everything the app needs inside it (code, libraries, settings). You can run it on any computer and it works the same way.

**Q: What is Kubernetes?**  
A: It's a system that manages many containers. It keeps them running, restarts them if they crash, and scales them up when needed. Think of it as a container supervisor.

**Q: What is Helm?**  
A: It's a package manager for Kubernetes. Like how you install apps on your phone from an app store, Helm installs apps on Kubernetes from charts.

**Q: What is Kind?**  
A: Kind = **K**ubernetes **IN** **D**ocker. It runs a full Kubernetes cluster inside Docker on your laptop. Free and no cloud needed!

**Q: Why 3 separate AI Employees instead of 1?**  
A: Separation of concerns — each does one job well. If one crashes, the others keep running. They can also scale independently.

---

## 🏆 Project Achievements

- ✅ **3 AI Employees** deployed and running
- ✅ **14 endpoints** all returning live data
- ✅ **Helm charts** for reproducible deployment
- ✅ **Auto-scaling** with HPA (1-5 replicas per service)
- ✅ **Monitoring** with Prometheus + Grafana
- ✅ **Landing page** dashboard at http://localhost:8080
- ✅ **One-command start** with `port-forward.ps1`
- ✅ **100+ files** of production-ready configuration
- ✅ **Beginner-friendly** documentation throughout

---

## 👨‍💻 Built With Love for AI Employee Hackathon 2026

*All tools used are free and open-source. No cloud account needed. Runs entirely on your laptop/pc.*
