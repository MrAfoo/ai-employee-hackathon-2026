# 🏆 Platinum Tier — Always-On Cloud + Local Executive

Cloud VM runs email/social watchers 24/7. Local laptop handles WhatsApp, payments, and approvals.

## Architecture

```
┌─────────────────────────────┐      Git Sync      ┌────────────────────────────┐
│   CLOUD VM (Oracle Free)    │ ◄─────────────────► │   LOCAL LAPTOP             │
│                             │                     │                            │
│  cloud_orchestrator.py      │    Vault/           │  local_agent.py            │
│  • Email triage             │    Needs_Action/    │  • WhatsApp replies        │
│  • LinkedIn drafts          │    Plans/           │  • Payment approval        │
│  • Social media drafts      │    Pending_Approval/│  • Final send/post         │
│  • Odoo sync                │    Done/            │  • Dashboard.md updates    │
│  • Health monitoring        │                     │  • HITL decisions          │
└─────────────────────────────┘                     └────────────────────────────┘
```

## Quick Start

### Cloud VM Setup (Ubuntu)
```bash
# Copy deploy_cloud.sh to your VM and run:
chmod +x deploy_cloud.sh
./deploy_cloud.sh
# Starts cloud_orchestrator as systemd service
```

### Local Laptop Setup (Windows)
```powershell
Copy-Item .env.example .env
# Fill in all credentials

# Set up startup task (runs local_agent.py on login)
.\setup_startup.ps1
```

## Task Claiming (Conflict Prevention)

Both agents can see the same Vault. To prevent double-processing:

```
Agent sees file in /Needs_Action/task.md
→ Moves it to /In_Progress/cloud_task.md   (atomic claim)
→ Works on it
→ Moves result to /Plans/ or /Pending_Approval/
→ Moves to /Done/
```

Only one agent can claim a file — the move is atomic.

## Credentials Needed

All credentials from Bronze + Silver + Gold tiers, plus:

| Credential | Required | How to Get |
|-----------|----------|-----------|
| `CLOUD_VM_IP` | ✅ Yes | Your Oracle/AWS VM public IP |
| `GIT_REPO_URL` | ✅ Yes | Private GitHub/GitLab repo for vault |
| `GIT_TOKEN` | ✅ Yes | GitHub Personal Access Token |
| `ODOO_URL` | For accounting | Odoo running on cloud VM |
| `HEALTH_ALERT_EMAIL` | For alerts | Your email for system alerts |
