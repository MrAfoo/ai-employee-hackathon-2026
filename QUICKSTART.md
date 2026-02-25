# AI Employee — Quick Start Guide

> Get your AI Employee running in under 10 minutes.

---

## What You Need

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| Git | Any | https://git-scm.com |
| Obsidian (optional) | Any | https://obsidian.md |

---

## Step 1 — Clone the Repo

```powershell
git clone https://github.com/MrAfoo/ai-employee-hackathon-2026.git
cd ai-employee-hackathon-2026
```

---

## Step 2 — Install Dependencies

```powershell
pip install -r BronzeTier/requirements.txt
playwright install chromium
```

---

## Step 3 — Set Up Credentials

```powershell
# Copy the template
Copy-Item BronzeTier\.env.example BronzeTier\.env

# Open and fill in your values
notepad BronzeTier\.env
```

**Minimum required to start:**
```env
GROQ_API_KEY=gsk_...          # Free at https://console.groq.com
VAULT_PATH=F:\path\to\Vault   # Your Obsidian vault path (use the Vault/ folder in this repo)
```

**Optional (for full features):**
```env
GMAIL_CREDENTIALS_PATH=...    # Gmail OAuth2 (see BronzeTier/setup_gmail_oauth.py)
GMAIL_TOKEN_PATH=...          # Auto-generated after OAuth2 setup
```

---

## Step 4 — Set Up Gmail OAuth2 (Optional)

```powershell
pip install google-api-python-client google-auth-oauthlib
python BronzeTier/setup_gmail_oauth.py
# Browser opens -> sign in -> grant permissions -> token.json saved automatically
```

---

## Step 5 — Set Up WhatsApp (Optional)

```powershell
# One-time QR scan (browser opens, scan with phone)
python BronzeTier/watchers/whatsapp_watcher.py --setup
# Press ENTER after chats load
```

---

## Step 6 — Launch Everything

```powershell
powershell -ExecutionPolicy Bypass -File start_all.ps1
```

This opens 4 terminal windows:
- **Watchdog** — keeps everything alive, auto-restarts crashes
- **HITL Monitor** — watches Vault/Approved/ and Vault/Rejected/
- **Email MCP** — sends emails on approval (port 8001)
- **Orchestrator** — main brain, polls Gmail + WhatsApp + Finance

---

## Step 7 — Test It

**Drop a test note:**
```powershell
# Create a test email note
@"
---
type: email
from: client@example.com
subject: Invoice Request
priority: high
---
Please send invoice for $1,200 project completion.
"@ | Out-File "Vault\Needs_Action\TEST_invoice.md" -Encoding utf8
```

**Watch what happens:**
1. Orchestrator detects new file (within 60s)
2. Groq reasons about it → writes `Vault/Plan.md`
3. Dashboard.md auto-updates
4. If amount > $500 → `Vault/Pending_Approval/` file created
5. Move it to `Vault/Approved/` → moves to `Vault/Done/` within 10s

---

## Folder Guide

```
Vault/
├── Needs_Action/      <- Drop anything here for AI to process
├── Pending_Approval/  <- AI puts sensitive actions here for your review
├── Approved/          <- Move files here to approve (AI executes)
├── Rejected/          <- Move files here to reject (AI archives)
├── Done/              <- Completed tasks land here
├── Finance_Drop/      <- Drop bank CSV files here
├── Accounting/        <- AI writes financial summaries here
├── Dashboard.md       <- Live status board (auto-updated)
└── Plan.md            <- AI's current action plan (auto-updated)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not set` | Add key to `BronzeTier/.env` |
| `Module not found` | Run `pip install -r BronzeTier/requirements.txt` |
| `WhatsApp not logged in` | Re-run `python BronzeTier/watchers/whatsapp_watcher.py --setup` |
| `Gmail auth error` | Re-run `python BronzeTier/setup_gmail_oauth.py` |
| `Orchestrator crashes` | Check `BronzeTier/orchestrator.log` for details |
| Files not moving to Done | Make sure `start_all.ps1` is running (HITL Monitor window) |

---

## Architecture Overview

```
[Gmail]      [WhatsApp]    [Bank CSV]    [File Drop]
    |              |             |              |
    +──────────────+─────────────+--------------+
                   |
              [Watchers] (Python scripts)
                   |
            [Vault/Needs_Action/]
                   |
            [Orchestrator.py]
                   |
             [Groq AI Reasoning]
                   |
        +──────────+──────────+
        |                     |
   [Plan.md]        [Pending_Approval/]
   [Dashboard.md]        |
                    [YOU review]
                         |
               +---------+---------+
               |                   |
          [Approved/]         [Rejected/]
               |                   |
          [Done/ - approved]  [Done/ - rejected]
```

---

> Full documentation: **README.md**
> Feature list: **FEATURES.md**
> Agent skills: **SKILLS.md**
> Hackathon spec: **hackathon.md**
