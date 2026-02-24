# 🏆 Platinum Tier Agent Skills

> Claude Code reads this file to discover all available skills in the Platinum Tier.
> Platinum Tier is Always-On Cloud + Local Executive — cloud VM runs heavy processing,
> local machine handles approvals, WhatsApp, payments, and final send/post.

---

## Skill: `cloud_orchestrate`
**Description:** Run the cloud orchestrator on Oracle/AWS VM — handles email triage, social drafts, Odoo sync, Plan.md generation. Writes tasks to shared vault via Git.
**Module:** `PlatinumTier/cloud_orchestrator.py`

```bash
# On Oracle VM:
python PlatinumTier/cloud_orchestrator.py \
  --vault ./Vault \
  --specialization "email_triage,draft_replies,social_drafts,odoo_sync"
```

**Cloud responsibilities:**
- Email triage (Gmail watcher + Groq reasoning)
- Social media draft generation
- Odoo P&L sync
- Plan.md generation
- Weekly CEO briefing draft

---

## Skill: `local_agent`
**Description:** Run the local agent on your laptop — handles WhatsApp (read-only), payments, HITL approvals, and final send/post actions.
**Module:** `PlatinumTier/local_agent.py`

```bash
# On your laptop:
python PlatinumTier/local_agent.py \
  --vault ./Vault \
  --specialization "approvals,whatsapp_sessions,banking,final_send"
```

**Local responsibilities:**
- HITL approval monitoring (`/Approved`, `/Rejected`)
- WhatsApp read-only session (Playwright)
- Banking/payment portal interactions
- Final email send (after approval)
- Dashboard.md updates (single writer)

---

## Skill: `vault_sync`
**Description:** Sync the Obsidian vault between cloud VM and local machine via Git. Pull → work → commit → push cycle.
**Module:** `PlatinumTier/vault_sync.py`

```python
from vault_sync import VaultSync
sync = VaultSync(vault_path="./Vault", sync_interval=30)
sync.start()  # Runs in background thread, syncs every 30s
```

**Git sync pattern:**
```
Cloud VM writes → git push
Local pulls      → git pull
Local writes     → git push
Cloud pulls      → git pull
```

**Conflict resolution:** Local agent is `single-writer` for `Dashboard.md`. Cloud agent writes to all other files.

---

## Skill: `claim_task`
**Description:** Atomically claim a task file from `/Needs_Action` by moving it to `/In_Progress/<agent>/`. Prevents two agents processing the same task.
**Module:** `PlatinumTier/claim_orchestrator.py`

```python
from claim_orchestrator import ClaimOrchestrator
claim = ClaimOrchestrator(vault_path="./Vault", agent_name="cloud")

# Claim a task (atomic move)
claimed = claim.claim_task("WHATSAPP_urgent_payment.md")
if claimed:
    # Process it...
    claim.complete_task("WHATSAPP_urgent_payment.md")
```

**Claim rule:** `/In_Progress/<agent>/` — only one agent holds the file at a time.

---

## Skill: `health_monitor`
**Description:** Monitor all MCP servers, vault sync, Odoo, and agent heartbeats. Send email alert after 3 consecutive failures.
**Module:** `PlatinumTier/health_monitor.py`

```bash
python PlatinumTier/health_monitor.py
# Checks every 60s, alerts on 3+ consecutive failures
```

**Monitors:**
| Component | Check | Alert Threshold |
|-----------|-------|----------------|
| Email MCP (port 8001) | HTTP GET /health | 3 failures |
| Odoo MCP (port 8004) | HTTP GET /health | 3 failures |
| Social MCP (port 8005) | HTTP GET /health | 3 failures |
| Vault sync | Git status | 5 min no sync |
| Disk space | `shutil.disk_usage` | < 500MB free |
| Needs_Action backlog | File count | > 20 files |

---

## Skill: `deploy_cloud`
**Description:** One-command Oracle/AWS VM setup — installs Python, dependencies, configures systemd service, starts cloud orchestrator.
**Module:** `PlatinumTier/deploy_cloud.sh`

```bash
# On Oracle VM (Ubuntu):
chmod +x PlatinumTier/deploy_cloud.sh
./PlatinumTier/deploy_cloud.sh

# What it does:
# 1. Updates system packages
# 2. Installs Python 3.11 + pip
# 3. Clones your GitHub repo
# 4. Installs requirements
# 5. Creates .env from template
# 6. Registers as systemd service (auto-start on boot)
```

---

## Skill: `setup_startup_local`
**Description:** Register all local agents as Windows startup tasks — runs automatically when you open your laptop.
**Module:** `PlatinumTier/setup_startup.ps1`

```powershell
powershell -ExecutionPolicy Bypass -File PlatinumTier/setup_startup.ps1

# Registers:
# - AI-Employee-LocalAgent    (on login)
# - AI-Employee-HealthMonitor (on login)
# - AI-Employee-VaultSync     (on login)
```

---

## Architecture: Cloud + Local Split

```
┌─────────────────────────────┐    Git Sync    ┌──────────────────────────────┐
│       ORACLE CLOUD VM       │ ◄────────────► │       YOUR LAPTOP            │
│                             │                │                              │
│  cloud_orchestrator.py      │                │  local_agent.py              │
│  ├─ Gmail Watcher           │                │  ├─ HITL Monitor             │
│  ├─ Groq Reasoning          │                │  ├─ WhatsApp (read-only)     │
│  ├─ Plan.md generation      │                │  ├─ Payment approvals        │
│  ├─ Social media drafts     │                │  ├─ Dashboard.md (writer)    │
│  ├─ Odoo P&L sync           │                │  └─ Final send/post          │
│  └─ CEO Briefing draft      │                │                              │
│                             │                │  health_monitor.py           │
│  Writes to:                 │                │  vault_sync.py               │
│  /Needs_Action              │                │                              │
│  /Plans                     │                │  Reads from:                 │
│  /Pending_Approval          │                │  /Pending_Approval           │
└─────────────────────────────┘                │  Writes to:                  │
                                               │  /Approved → /Done           │
                                               │  Dashboard.md                │
                                               └──────────────────────────────┘
```

---

## Delegation Paths

| Path | Writer | Reader |
|------|--------|--------|
| `/Needs_Action` | Cloud | Local |
| `/Plans` | Cloud | Local |
| `/Pending_Approval` | Cloud | Local (you) |
| `/Approved` | You | Local agent |
| `/Rejected` | You | Local agent |
| `/Done` | Local agent | Both |
| `Dashboard.md` | Local agent only | Both |
| `/Updates` | Both | Both |

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `VAULT_PATH` | ✅ | Absolute path to vault |
| `VAULT_GIT_REMOTE` | ✅ | GitHub repo URL for vault sync |
| `CLOUD_VM_IP` | ✅ | Oracle VM public IP |
| `AGENT_NAME` | ✅ | `cloud` or `local` |
| `ODOO_URL` | ✅ Odoo | Odoo server URL |
| `HEALTH_ALERT_EMAIL` | ✅ | Email for health alerts |
