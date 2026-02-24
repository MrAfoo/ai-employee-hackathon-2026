# Architecture & Lessons Learned
## Bronze → Silver → Gold → Platinum Autonomous AI Agent Stack

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              PLATINUM TIER – Always-On Cloud + Local Executive   │
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │   CLOUD VM (Oracle/AWS)  │  │   LOCAL LAPTOP               │ │
│  │  cloud_orchestrator.py   │  │  local_agent.py              │ │
│  │  • Email triage          │  │  • WhatsApp sessions         │ │
│  │  • Social/LinkedIn drafts│  │  • Payment approvals         │ │
│  │  • Odoo (cloud)          │  │  • Final send/post           │ │
│  │  • Always-on watchers    │  │  • Dashboard (single writer) │ │
│  └─────────────┬────────────┘  └──────────────┬───────────────┘ │
│                │   Git-Synced Obsidian Vault   │                 │
│                └──────────────┬───────────────┘                 │
│                    vault_sync.py (30s interval)                  │
│  claim_orchestrator.py (claim-by-move: /In_Progress/<agent>)    │
│  health_monitor.py (checks MCP + vault + Odoo, alerts on fail)  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     GOLD TIER – Autonomous Employee              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Odoo MCP     │  │ Social MCP   │  │ Multi-MCP Orchestrator ││
│  │ :8004        │  │ :8005        │  │ (ralph_wiggum_loop)    ││
│  └──────────────┘  └──────────────┘  └────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Audit Logger │  │ CEO Briefing │  │ Error Recovery         ││
│  └──────────────┘  └──────────────┘  └────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                  SILVER TIER – Functional Assistant              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Email MCP    │  │ LinkedIn MCP │  │ Claude Reasoning Loop  ││
│  │ :8001        │  │ :8002        │  │ (Plan.md generator)    ││
│  └──────────────┘  └──────────────┘  └────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ WhatsApp     │  │ LinkedIn     │  │ Human-in-the-Loop      ││
│  │ Watcher      │  │ Watcher      │  │ Approval Gate          ││
│  └──────────────┘  └──────────────┘  └────────────────────────┘│
│  ┌────────────────────────────────────────────────────────────┐ │
│  │          Windows Task Scheduler (setup_tasks.ps1)          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                    BRONZE TIER – Foundation                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Gmail Watcher│  │ FS Watcher   │  │ Obsidian Vault         ││
│  │ (IMAP)       │  │ (watchdog)   │  │ Inbox/Needs_Action/Done││
│  └──────────────┘  └──────────────┘  └────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ VaultSkill   │  │ WatcherSkill │  Agent Skills Registry     │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │     Groq API       │
                    │  (Llama / Mixtral) │
                    └────────────────────┘
```

---

## Component Index

| Component | File | Tier | Port |
|-----------|------|------|------|
| Gmail Watcher | `BronzeTier/watchers/gmail_watcher.py` | Bronze | — |
| Filesystem Watcher | `BronzeTier/watchers/filesystem_watcher.py` | Bronze | — |
| Vault Skill | `BronzeTier/skills/vault_skill.py` | Bronze | — |
| Watcher Skill | `BronzeTier/skills/watcher_skill.py` | Bronze | — |
| Skills Registry | `BronzeTier/skills/registry.py` | Bronze | — |
| WhatsApp Watcher | `SilverTier/watchers/whatsapp_watcher.py` | Silver | 8003 (webhook) |
| LinkedIn Watcher | `SilverTier/watchers/linkedin_watcher.py` | Silver | — |
| Email MCP Server | `SilverTier/mcp_servers/email_mcp_server.py` | Silver | 8001 |
| LinkedIn MCP Server | `SilverTier/mcp_servers/linkedin_mcp_server.py` | Silver | 8002 |
| Reasoning Loop | `SilverTier/reasoning/reasoning_loop.py` | Silver | — |
| Approval Gate | `SilverTier/reasoning/approval.py` | Silver | — |
| Task Scheduler | `SilverTier/scheduler/setup_tasks.ps1` | Silver | — |
| Odoo MCP Server | `GoldTier/mcp_servers/odoo_mcp_server.py` | Gold | 8004 |
| Social Media MCP | `GoldTier/mcp_servers/social_media_mcp_server.py` | Gold | 8005 |
| Multi-MCP Orchestrator | `GoldTier/orchestrator/multi_mcp_orchestrator.py` | Gold | — |
| Ralph Wiggum Loop | `GoldTier/orchestrator/ralph_wiggum_loop.py` | Gold | — |
| Audit Logger | `GoldTier/audit/audit_logger.py` | Gold | — |
| CEO Briefing | `GoldTier/briefing/ceo_briefing.py` | Gold | — |
| Cloud Orchestrator | `PlatinumTier/cloud_orchestrator.py` | Platinum | — |
| Local Agent | `PlatinumTier/local_agent.py` | Platinum | — |
| Vault Sync | `PlatinumTier/vault_sync.py` | Platinum | — |
| Claim Orchestrator | `PlatinumTier/claim_orchestrator.py` | Platinum | — |
| Health Monitor | `PlatinumTier/health_monitor.py` | Platinum | — |
| Cloud Deploy | `PlatinumTier/deploy_cloud.sh` | Platinum | — |
| Local Startup | `PlatinumTier/setup_startup.ps1` | Platinum | — |

---

## Data Flow

```
External Signal (email / file / WhatsApp / LinkedIn)
        │
        ▼
   Watcher Script
        │  writes
        ▼
  Vault Inbox (.md note)
        │
        ▼
  Reasoning Loop (Claude)
        │  reads Inbox + Needs_Action
        │  generates Plan.md
        ▼
  Ralph Wiggum Loop (Claude + Tools)
        │  calls MCP servers
        ├──▶ Email MCP → SMTP → recipient
        ├──▶ LinkedIn MCP → LinkedIn API
        ├──▶ Social MCP → Twitter / Facebook / Instagram
        ├──▶ Odoo MCP → Odoo JSON-RPC → accounting record
        └──▶ VaultSkill → Done folder (note archived)
        │
        ▼
  Audit Logger (JSONL)
        │
        ▼
  CEO Briefing (weekly, Monday 08:00)
        │  emails to CEO via Email MCP
        ▼
  Vault: CEO_Briefing_YYYY-WW.md
```

---

## Design Principles

### 1. Modular Agent Skills
Every capability is a Python class with `run(action, **kwargs)` and `describe()` methods. This makes skills composable, testable, and easy to add/remove without touching other components.

### 2. MCP Server Pattern
Each external system (email, LinkedIn, Odoo, social media) gets its own FastAPI micro-server. Benefits:
- Claude can call any server via HTTP (language-agnostic)
- Servers can be deployed independently or as a monolith
- Easy to mock for testing
- Human-in-the-loop approval is built into each server's queue

### 3. Human-in-the-Loop by Default
All sensitive outbound actions (sending emails, posting, creating invoices) default to `require_approval=True`. The approval gate (`approval.py`) provides CLI prompts with audit logging. Set `AUTO_APPROVE=true` only for fully trusted automation.

### 4. Vault as the Source of Truth
The Obsidian vault (`Inbox / Needs_Action / Done`) is the single shared state between all components. Watchers write; the reasoning loop reads; the Ralph Wiggum loop archives. No database required at Bronze/Silver tier.

### 5. Ralph Wiggum Loop (Agentic Iteration)
Named for relentless optimism. Claude receives a task + tool definitions and iterates — calling one tool at a time, processing results, then deciding the next step — until it calls `task_complete`. The loop has a configurable `max_iterations` safety cap and full audit trail.

### 6. Error Recovery Layering
- **Watcher level**: reconnect with exponential backoff (30s)
- **MCP call level**: 3 retries with doubling backoff via `multi_mcp_orchestrator.call_mcp()`
- **Function level**: `@with_recovery` decorator for any business logic
- **Audit level**: all failures written to `errors.jsonl` for CEO briefing

---

## Lessons Learned

### ✅ What Worked Well
- **Filesystem-based vault** requires zero infrastructure. Obsidian gives a free, powerful UI.
- **IMAP polling** is simpler and more reliable than Gmail push for small-scale automation.
- **FastAPI for MCP servers** — automatic OpenAPI docs, Pydantic validation, easy to extend.
- **Groq tool_use** (OpenAI-compatible function calling) with structured JSON schemas produces consistent, parseable outputs.
- **Modular skills registry** made it trivial to add new capabilities without refactoring.

### ⚠️ Watch Out For
- **Gmail App Passwords** require 2FA to be enabled on the Google account first.
- **LinkedIn API** heavily rate-limits and restricts notification/message access — partner access required for full functionality. The watcher gracefully degrades.
- **WhatsApp Business API** requires a verified business account. Use export mode for personal use.
- **Odoo Community** must have XML-RPC/JSON-RPC enabled (it is by default).
- **Windows Task Scheduler** requires Administrator rights to register tasks. Run `setup_tasks.ps1` as Admin.
- **`require_approval=True` defaults** prevent accidental mass-posting during development.

### 🔮 Future Extensions
- **Vector memory**: Add a ChromaDB or Qdrant skill to give Claude long-term memory of past plans and outcomes.
- **Slack/Teams MCP**: Add an inbound webhook watcher and outbound message server.
- **GitHub MCP**: Watch PRs, issues, and CI results; auto-triage to vault.
- **Voice briefing**: Convert CEO Briefing to audio via ElevenLabs MCP.
- **Multi-agent**: Run parallel Ralph Wiggum loops for different domains (sales, ops, finance) with a coordinator agent.
- **Kubernetes deployment**: Each MCP server is already containerisable — add Dockerfiles and Helm charts following the Phase2/Phase5 patterns in this repo.

---

## Quick Start: Full Stack

```powershell
# 1. Configure environment
Copy-Item BronzeTier\.env.example BronzeTier\.env
Copy-Item SilverTier\.env.example SilverTier\.env
Copy-Item GoldTier\.env.example GoldTier\.env
Copy-Item PlatinumTier\.env.example PlatinumTier\.env
# Edit all .env files with your credentials

# 2. Install dependencies
pip install -r BronzeTier\requirements.txt
pip install -r SilverTier\requirements.txt
pip install -r GoldTier\requirements.txt
pip install -r PlatinumTier\requirements.txt

# 3. Start MCP servers (separate terminals)
python SilverTier\mcp_servers\email_mcp_server.py
python SilverTier\mcp_servers\linkedin_mcp_server.py
python GoldTier\mcp_servers\odoo_mcp_server.py
python GoldTier\mcp_servers\social_media_mcp_server.py

# 4. Register scheduled tasks (Admin PowerShell)
.\SilverTier\scheduler\setup_tasks.ps1

# 5. Run reasoning loop once
python SilverTier\reasoning\reasoning_loop.py

# 6. Run an autonomous task
python GoldTier\orchestrator\ralph_wiggum_loop.py --task "Summarise this week's emails and draft a LinkedIn post"

# 7. Generate CEO briefing
python GoldTier\briefing\ceo_briefing.py --email ceo@yourcompany.com
```

---

## Quick Start: Platinum Tier

### On Cloud VM (Oracle Free / AWS EC2 – Ubuntu)
```bash
# One-time setup
chmod +x PlatinumTier/deploy_cloud.sh
./PlatinumTier/deploy_cloud.sh

# Fill in credentials
nano PlatinumTier/.env

# Start (systemd service auto-installed)
sudo systemctl start ai-employee-cloud
sudo journalctl -u ai-employee-cloud -f
```

### On Local Laptop (Windows)
```powershell
# One-time setup (run as Administrator)
.\PlatinumTier\setup_startup.ps1

# Fill in credentials
notepad PlatinumTier\.env

# Start immediately
Start-ScheduledTask -TaskName "AIEmployee-LocalAgent"

# Watch logs
Get-Content PlatinumTier\local_agent.log -Wait
```

### Vault Folder Flow
```
Watcher → /Inbox
        → /Needs_Action
               ↓ claim-by-move
     /In_Progress/cloud   /In_Progress/local
               ↓                   ↓
           /Plans         /Pending_Approval
                                   ↓ (human moves file)
                          /Approved  /Rejected
                                   ↓
                               /Done
```
