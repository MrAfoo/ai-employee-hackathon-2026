# 🥉 Bronze Tier — Foundation Layer

The local engine: watchers, vault, Groq reasoning, and HITL approval.

## Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Set up credentials
Copy-Item .env.example .env
# Edit .env — fill in GROQ_API_KEY and VAULT_PATH at minimum

# 3. Set up Gmail (one-time)
python setup_gmail_oauth.py

# 4. Start (from repo root)
.\start_all.ps1
# OR start just the orchestrator:
python Orchestrator.py
```

## Files

| File | Purpose |
|------|---------|
| `Orchestrator.py` | **Master orchestrator** — start here |
| `hitl_orchestrator.py` | Watches `/Approved` + `/Rejected` folders |
| `error_recovery.py` | Retry logic, quarantine, error categories |
| `watchdog_monitor.py` | Auto-restarts Orchestrator if it crashes |
| `setup_gmail_oauth.py` | One-time Gmail OAuth2 browser flow |
| `mcp_config.json` | Claude Code MCP server configuration |

## Watchers

| Watcher | Trigger | Output |
|---------|---------|--------|
| `gmail_watcher.py` | Unread important Gmail | `Needs_Action/EMAIL_*.md` |
| `whatsapp_watcher.py` | Keyword messages on WhatsApp Web | `Needs_Action/WHATSAPP_*.md` |
| `filesystem_watcher.py` | New file in `Vault/Drop/` | `Needs_Action/FILE_*.md` |
| `finance_watcher.py` | CSV in `Vault/Finance_Drop/` | `Accounting/Current_Month.md` |

## HITL Safeguards

Actions that require your approval:
- Any payment > $500
- Wire transfer requests  
- Sending emails on your behalf
- Social media posting

**How to approve:** Move the `APPROVAL_REQUIRED_*.md` file from `Vault/Pending_Approval/` to `Vault/Approved/`

**How to reject:** Move to `Vault/Rejected/`

## Credentials Needed

| Credential | Required | How to Get |
|-----------|----------|-----------|
| `GROQ_API_KEY` | ✅ Yes | [console.groq.com](https://console.groq.com) — free |
| `VAULT_PATH` | ✅ Yes | Path to your `Vault/` folder |
| `GMAIL_CREDENTIALS_PATH` | ✅ For Gmail | Google Cloud Console → Gmail API |
| `GMAIL_TOKEN_PATH` | ✅ For Gmail | Auto-created by `setup_gmail_oauth.py` |
| `WHATSAPP_SESSION_PATH` | For WhatsApp | Auto-created on first run |
