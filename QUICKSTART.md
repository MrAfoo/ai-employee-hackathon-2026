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
VAULT_PATH=./BronzeTier/Vault  # Single vault — do NOT change this
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

## Step 5 — Set Up WhatsApp

WhatsApp uses the **Meta Business Cloud API** (no QR scan needed).

```powershell
# 1. Go to https://developers.facebook.com → Your App → WhatsApp → API Setup
# 2. Add your number as a test recipient (e.g. 923713584557)
# 3. Generate a 60-day access token and set in BronzeTier/.env:
#    WHATSAPP_API_TOKEN=your_60_day_token
#    WHATSAPP_PHONE_NUMBER_ID=your_phone_id
# 4. Webhook URL: https://your-ngrok-url/webhook/whatsapp
#    Verify token: myhackathonverifytoken
```

**To reply to a WhatsApp message:**
```powershell
# Option 1 — Browser (quick):
# http://localhost:3000/reply/whatsapp/923713584557?msg=Hello+there

# Option 2 — PowerShell:
Invoke-RestMethod -Uri http://localhost:3000/reply/whatsapp `
  -Method POST `
  -Body '{"to":"923713584557","message":"Hello!"}' `
  -ContentType "application/json"

# Option 3 — Move approval file to BronzeTier/Vault/Approved/ → AI auto-replies
```

---

## Step 6 — Launch Everything

```powershell
powershell -ExecutionPolicy Bypass -File start_all.ps1
```

This opens **6 terminal windows**:
- **WhatsApp Webhook** — receives messages on port 3000
- **ngrok Tunnel** — exposes webhook to Meta Cloud API
- **HITL Monitor** — watches `BronzeTier/Vault/Approved/` and `/Rejected/`
- **Watchdog** — keeps everything alive, auto-restarts crashes
- **Email MCP** — sends emails on approval (port 8001)
- **Orchestrator** — main brain, polls Gmail + WhatsApp + Finance

---

## Step 7 — Test It

**Test WhatsApp (send a message to +1 555 145 8166):**
- Normal message → saved in `BronzeTier/Vault/Needs_Action/WHATSAPP_*.md`
- Message with `urgent`/`asap`/`money`/`help` → **Priority: HIGH** → Orchestrator auto-triggered

**Test email note:**
```powershell
@"
---
type: email
from: client@example.com
subject: Invoice Request
priority: high
---
Please send invoice for $1,200 project completion.
"@ | Out-File "BronzeTier\Vault\Needs_Action\TEST_invoice.md" -Encoding utf8
```

**Watch what happens:**
1. Orchestrator detects new file (within 60s)
2. Groq reasons about it → writes `BronzeTier/Vault/Plan.md`
3. Dashboard.md auto-updates
4. If amount > $500 → `BronzeTier/Vault/Pending_Approval/` file created
5. Move it to `BronzeTier/Vault/Approved/` → HITL executes action → moves to `Done/` within 10s

---

## Folder Guide

```
BronzeTier/Vault/       ← Single vault for ALL services
├── Needs_Action/       ← Email/WhatsApp/files land here automatically
├── Pending_Approval/   ← AI puts sensitive actions here for YOUR review
├── Approved/           ← Move files here → AI auto-executes + replies
├── Rejected/           ← Move files here → AI archives, no action taken
├── Done/               ← Completed tasks land here
├── Finance_Drop/       ← Drop bank CSV files here
├── Accounting/         ← AI writes financial summaries here
├── Dashboard.md        ← Live status board (auto-updated)
└── Plan.md             ← AI's current action plan (auto-updated)
```

## WhatsApp Reply Options

| Method | Command |
|--------|---------|
| Browser | `http://localhost:3000/reply/whatsapp/PHONE?msg=Your+message` |
| PowerShell | `Invoke-RestMethod -Uri http://localhost:3000/reply/whatsapp -Method POST -Body '{"to":"PHONE","message":"Hello"}' -ContentType "application/json"` |
| HITL Auto | Move file from `Pending_Approval/` → `Approved/` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not set` | Add key to `BronzeTier/.env` |
| `Module not found` | Run `pip install -r BronzeTier/requirements.txt` |
| `WhatsApp token expired` | Get new 60-day token from Meta developer portal |
| `ngrok not found` | Install ngrok: `winget install ngrok` or download from ngrok.com |
| `Gmail auth error` | Re-run `python BronzeTier/setup_gmail_oauth.py` |
| `Orchestrator crashes` | Check `BronzeTier/orchestrator.log` for details |
| Files not moving to Done | Make sure `start_all.ps1` is running (HITL Monitor window) |
| WhatsApp message not received | Check ngrok is running at `http://localhost:4040` |

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
