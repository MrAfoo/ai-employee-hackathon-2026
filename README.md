# 🤖 AI Employee — Bronze → Silver → Gold → Platinum

> An autonomous AI agent system that monitors your communications, reasons about them using Groq LLM, and acts on your behalf — with human-in-the-loop safeguards for sensitive actions.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OBSIDIAN VAULT (GUI + Memory)                │
│  Dashboard.md │ Plan.md │ Company_Handbook.md │ Needs_Action/ Done/ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ read/write .md files
┌────────────────────────────▼────────────────────────────────────────┐
│                    ORCHESTRATOR  (BronzeTier/Orchestrator.py)        │
│   Perception → Reasoning (Groq LLM) → Action → HITL Approval        │
└──────┬──────────────────────────────────────────────────┬───────────┘
       │ watchers                                         │ MCP actions
┌──────▼──────────┐                            ┌──────────▼──────────┐
│   WATCHERS      │                            │   MCP SERVERS       │
│ • Gmail (OAuth2)│                            │ • Email MCP :8001   │
│ • WhatsApp Web  │                            │ • LinkedIn MCP      │
│ • Filesystem    │                            │ • Odoo MCP          │
│ • Finance CSV   │                            │ • Social Media MCP  │
└─────────────────┘                            └─────────────────────┘
```

---

## 📊 Tier Overview

| Tier | Status | Description |
|------|--------|-------------|
| 🥉 **Bronze** | ✅ Working | Local engine: watchers, vault, Groq reasoning, HITL |
| 🥈 **Silver** | ✅ Ready | Multi-watcher, LinkedIn posting, MCP email server |
| 🥇 **Gold** | ✅ Ready | Odoo accounting, social media, CEO briefing, Ralph Wiggum loop |
| 🏆 **Platinum** | ✅ Ready | Cloud VM + local split, Git vault sync, health monitoring |

---

## ⚡ Quick Start (Bronze Tier — 5 minutes)

### 1. Clone & Install
```powershell
git clone <your-repo>
cd AI-Employee-Hackathon-2026
pip install -r BronzeTier/requirements.txt
```

### 2. Set Up Credentials
```powershell
Copy-Item BronzeTier\.env.example BronzeTier\.env
# Edit BronzeTier\.env — minimum required:
#   GROQ_API_KEY       → https://console.groq.com (free)
#   VAULT_PATH         → path to your Vault/ folder
#   GMAIL_CREDENTIALS_PATH → from Google Cloud Console
#   GMAIL_TOKEN_PATH   → will be auto-created
```

### 3. Authenticate Gmail (one-time)
```powershell
python BronzeTier/setup_gmail_oauth.py
# Browser opens → sign in → click Advanced → Go to app (unsafe) → Allow
```

### 4. Launch Everything
```powershell
.\start_all.ps1
```

---

## 🔁 The Perception → Reasoning → Action Loop

```
1. PERCEIVE   Watcher detects new email/WhatsApp/file
              → Creates .md note in Vault/Needs_Action/

2. REASON     Orchestrator reads all Needs_Action notes
              → Sends to Groq LLM → Gets structured JSON plan
              → Writes Plan.md with checkboxes

3. ACT        If safe: executes via MCP server
              If sensitive (>$500, payments, wire transfers):
              → Creates APPROVAL_REQUIRED_*.md in Vault/Pending_Approval/
              → WAITS for you to move file to Vault/Approved/
              → Then executes and moves to Vault/Done/
```

---

## 📁 Folder Structure

```
AI-Employee-Hackathon-2026/
│
├── Vault/                          ← Obsidian vault (your GUI + memory)
│   ├── Dashboard.md                ← Real-time agent status
│   ├── Company_Handbook.md         ← Rules of engagement
│   ├── Plan.md                     ← AI-generated action plan
│   ├── Needs_Action/               ← Inbox for watcher-created notes
│   ├── Done/                       ← Completed/processed items
│   ├── Pending_Approval/           ← Awaiting your approval
│   ├── Approved/                   ← Move files here to approve
│   ├── Rejected/                   ← Move files here to reject
│   ├── Inbox/                      ← Raw incoming notes
│   ├── Drop/                       ← Drop any file for processing
│   ├── Finance_Drop/               ← Drop bank CSVs here
│   ├── Accounting/                 ← Auto-generated finance logs
│   └── Quarantine/                 ← Corrupted/suspicious files
│
├── BronzeTier/                     ← Foundation layer
│   ├── Orchestrator.py             ← Master orchestrator (START HERE)
│   ├── hitl_orchestrator.py        ← Human-in-the-loop approval watcher
│   ├── error_recovery.py           ← Error handling + retry logic
│   ├── watchdog_monitor.py         ← Auto-restart if orchestrator crashes
│   ├── setup_gmail_oauth.py        ← One-time Gmail OAuth2 setup
│   ├── mcp_config.json             ← Claude Code MCP server config
│   ├── requirements.txt
│   ├── .env.example                ← Copy to .env and fill in
│   ├── watchers/
│   │   ├── base_watcher.py         ← Abstract base class for all watchers
│   │   ├── gmail_watcher.py        ← Gmail API (OAuth2) watcher
│   │   ├── whatsapp_watcher.py     ← WhatsApp Web (Playwright) watcher
│   │   ├── filesystem_watcher.py   ← Drop folder watcher (watchdog)
│   │   ├── finance_watcher.py      ← CSV/bank transaction watcher
│   │   └── ralph_wiggum_hook.py    ← Claude Code Stop hook
│   └── skills/
│       ├── vault_skill.py          ← Read/write/move vault notes
│       ├── watcher_skill.py        ← Launch watcher threads
│       └── registry.py             ← Modular skill registry
│
├── SilverTier/                     ← Functional assistant layer
│   ├── watchers/
│   │   ├── whatsapp_watcher.py     ← Enhanced WhatsApp watcher
│   │   └── linkedin_watcher.py     ← LinkedIn activity watcher
│   ├── mcp_servers/
│   │   ├── email_mcp_server.py     ← FastAPI email server (port 8001)
│   │   └── linkedin_mcp_server.py  ← LinkedIn posting MCP server
│   ├── reasoning/
│   │   ├── reasoning_loop.py       ← Groq-powered Plan.md generator
│   │   └── approval.py             ← Approval prompt helpers
│   └── scheduler/
│       └── setup_tasks.ps1         ← Windows Task Scheduler setup
│
├── GoldTier/                       ← Autonomous employee layer
│   ├── orchestrator/
│   │   ├── multi_mcp_orchestrator.py ← Routes actions to MCP servers
│   │   └── ralph_wiggum_loop.py    ← Autonomous multi-step loop
│   ├── mcp_servers/
│   │   ├── odoo_mcp_server.py      ← Odoo accounting via JSON-RPC
│   │   └── social_media_mcp_server.py ← Facebook/LinkedIn posting
│   ├── audit/
│   │   └── audit_logger.py         ← JSONL structured audit log
│   ├── briefing/
│   │   └── ceo_briefing.py         ← Weekly CEO briefing generator
│   └── ARCHITECTURE.md             ← Full system architecture docs
│
├── PlatinumTier/                   ← Always-on cloud + local split
│   ├── cloud_orchestrator.py       ← Runs on Oracle/AWS VM
│   ├── local_agent.py              ← Runs on your laptop
│   ├── vault_sync.py               ← Git-based vault sync
│   ├── claim_orchestrator.py       ← Atomic task claiming
│   ├── health_monitor.py           ← System health checks + alerts
│   ├── deploy_cloud.sh             ← Ubuntu VM setup script
│   └── setup_startup.ps1           ← Windows startup config
│
├── start_all.ps1                   ← ONE-CLICK STARTUP (run this!)
├── .gitignore                      ← Protects .env, tokens, sessions
└── README.md                       ← This file
```

---

## ✅ Features: What's Working

### 🥉 Bronze Tier
| Feature | Status | Notes |
|---------|--------|-------|
| Groq LLM reasoning | ✅ **Working** | llama-3.3-70b-versatile, free tier |
| Gmail OAuth2 watcher | ✅ **Working** | Reads unread important emails |
| Filesystem drop watcher | ✅ **Working** | Drop any file → auto-processed |
| Finance CSV watcher | ✅ **Working** | Drop CSV → logged to Accounting/ |
| HITL approval flow | ✅ **Working** | Move to /Approved → executes → Done |
| Status tracking | ✅ **Working** | pending → processed/approved/rejected |
| Plan.md generation | ✅ **Working** | Groq generates structured action plan |
| Error recovery | ✅ **Working** | Exponential backoff, quarantine, alerts |
| Watchdog auto-restart | ✅ **Working** | Restarts orchestrator on crash |
| Ralph Wiggum hook | ✅ **Ready** | Claude Code Stop hook |
| WhatsApp watcher | ⚠️ **Needs setup** | Run once with headless=False to scan QR |
| Gmail sending (SMTP) | ⚠️ **Needs app password** | Add GMAIL_APP_PASSWORD to .env |

### 🥈 Silver Tier
| Feature | Status | Notes |
|---------|--------|-------|
| Email MCP server | ✅ **Ready** | `python SilverTier/mcp_servers/email_mcp_server.py` |
| LinkedIn MCP server | ✅ **Ready** | Needs LINKEDIN_ACCESS_TOKEN |
| Reasoning loop | ✅ **Ready** | `python SilverTier/reasoning/reasoning_loop.py` |
| WhatsApp watcher | ⚠️ **Needs QR scan** | First run headless=False |
| Windows Task Scheduler | ✅ **Ready** | Run setup_tasks.ps1 once |

### 🥇 Gold Tier
| Feature | Status | Notes |
|---------|--------|-------|
| Multi-MCP orchestrator | ✅ **Ready** | Routes to email/social/odoo MCPs |
| Ralph Wiggum loop | ✅ **Ready** | Autonomous until task complete |
| Odoo MCP server | ⚠️ **Needs Odoo** | Install Odoo Community locally |
| Social media MCP | ⚠️ **Needs tokens** | Facebook/LinkedIn tokens in .env |
| CEO briefing | ✅ **Ready** | Generates weekly Markdown briefing |
| Audit logging | ✅ **Ready** | JSONL structured logs |

### 🏆 Platinum Tier
| Feature | Status | Notes |
|---------|--------|-------|
| Cloud orchestrator | ✅ **Ready** | Deploy with deploy_cloud.sh |
| Local agent | ✅ **Ready** | Handles WhatsApp, payments, approvals |
| Git vault sync | ✅ **Ready** | Needs private Git repo |
| Health monitoring | ✅ **Ready** | Email alerts on 3 consecutive failures |
| Claim orchestrator | ✅ **Ready** | Atomic task claiming by move |

---

## 🔐 Security & Credential Handling

### What's Protected
- All `.env` files → in `.gitignore` (never committed)
- `credentials.json`, `token.json` → in `.gitignore`
- `whatsapp_session/` → in `.gitignore`
- `logs/`, `*.jsonl` → in `.gitignore`
- `Vault/Accounting/`, `Vault/Approved/` → in `.gitignore`

### Credential Storage
```
BronzeTier/.env          ← your secrets (NEVER commit this)
BronzeTier/.env.example  ← safe template (committed, no real values)
```

### HITL Safeguards
- Any payment > `$500` → blocked, requires manual approval
- Wire transfer requests → always blocked
- Email sending → only after you move file to `/Approved`
- LinkedIn/social posting → requires approval
- Rejection → move file to `/Rejected` → logged, no action taken

---

## 🎬 Demo: Full End-to-End Flow

```powershell
# Step 1: Start everything
.\start_all.ps1

# Step 2: Drop a test note (simulates incoming email)
Copy-Item BronzeTier/watchers/base_watcher.py Vault/Drop/test_drop.py

# OR create a test email note:
@"
---
type: email
from: client@example.com
subject: Invoice Request - $1200
priority: high
status: pending
---
Please send invoice for Project Alpha Milestone 2 - $1,200.
"@ | Out-File Vault/Needs_Action/TEST_invoice.md

# Step 3: Watch Orchestrator reason about it (in Terminal 1)
# → Plan.md gets updated
# → APPROVAL_REQUIRED_*.md appears in Vault/Pending_Approval/

# Step 4: Open Vault/Pending_Approval/ in Obsidian
# Review the approval request

# Step 5: Approve it
Move-Item Vault/Pending_Approval/APPROVAL_REQUIRED_*.md Vault/Approved/

# Step 6: Within 10 seconds → file moves to Vault/Done/ with status: approved
Get-ChildItem Vault/Done/
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `GROQ_API_KEY` not found | Copy `.env.example` → `.env`, fill in key |
| Gmail OAuth2 `access_denied` | Click "Advanced" → "Go to app (unsafe)" in browser |
| File stuck in `/Approved` | Make sure Orchestrator is running first |
| WhatsApp QR not scanning | Run with `headless=False` in whatsapp_watcher.py |
| Orchestrator crashes | Run `watchdog_monitor.py` instead — auto-restarts |
| `status: pending` in Done | Fixed — now shows `status: processed/approved/rejected` |

---

## 📞 Support & Contributing

See `CONTRIBUTING.md` for guidelines.
Report bugs via GitHub Issues.
