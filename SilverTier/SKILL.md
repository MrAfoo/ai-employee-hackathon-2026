# 🥈 Silver Tier Agent Skills

> Claude Code reads this file to discover all available skills in the Silver Tier.
> Silver Tier extends Bronze with multi-source watchers, MCP servers, LinkedIn posting,
> reasoning loop, human-in-the-loop approval, and Windows Task Scheduler integration.

---

## Skill: `reasoning_loop`
**Description:** Read all notes from `/Needs_Action` + `/Inbox`, send to Groq, generate a structured `Plan.md` with prioritised action items.
**Module:** `SilverTier/reasoning/reasoning_loop.py`

```bash
python SilverTier/reasoning/reasoning_loop.py \
  --vault ./Vault \
  --model llama-3.3-70b-versatile
```

**Output:** `Vault/Plan.md` with sections:
- 🔴 Urgent (do today)
- 🟡 This Week
- 🟢 Backlog
- 💡 Opportunities
- 📧 Emails to Send
- 📱 Posts to Draft
- 🔁 Next Loop Notes

---

## Skill: `send_email`
**Description:** Send a real email via Gmail SMTP through the Email MCP server.
**Module:** `SilverTier/mcp_servers/email_mcp_server.py`
**Endpoint:** `POST http://localhost:8001/send-email`

```python
import httpx
response = httpx.post("http://localhost:8001/send-email", json={
    "to": "client@example.com",
    "subject": "Invoice #1234",
    "body": "Please find attached your invoice...",
    "cc": [],
    "reply_to": ""
})
```

**Start server:**
```bash
python SilverTier/mcp_servers/email_mcp_server.py
# Runs on port 8001
```

**Env vars required:** `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD`

---

## Skill: `draft_email`
**Description:** Save an email draft to `Vault/Drafts/` for review before sending.
**Module:** `SilverTier/mcp_servers/email_mcp_server.py`
**Endpoint:** `POST http://localhost:8001/draft-email`

```python
response = httpx.post("http://localhost:8001/draft-email", json={
    "to": "client@example.com",
    "subject": "Invoice #1234",
    "body": "Draft content here..."
})
```

---

## Skill: `post_linkedin`
**Description:** Draft and publish a LinkedIn post. Groq writes the post, HITL approves it, then it publishes automatically.
**Module:** `SilverTier/linkedin_integration.py`

```bash
# Draft a post (goes to Vault/Pending_Approval/)
python SilverTier/linkedin_integration.py --draft "Weekly business update topic"

# Publish approved posts from Vault/Approved/
python SilverTier/linkedin_integration.py --publish

# Check your profile info
python SilverTier/linkedin_integration.py --profile
```

**Flow:**
1. Groq drafts the post content
2. Post saved to `Vault/Pending_Approval/LINKEDIN_POST_*.md`
3. You review and move to `Vault/Approved/`
4. `--publish` sends it to LinkedIn

**Env vars required:** `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_ID`

---

## Skill: `watch_whatsapp_extended`
**Description:** Extended WhatsApp watcher with keyword filtering, contact priority lists, and multi-chat monitoring.
**Module:** `SilverTier/watchers/whatsapp_watcher.py`

```python
from watchers.whatsapp_watcher import WhatsAppWatcher
watcher = WhatsAppWatcher(
    vault_path="./Vault",
    session_path="./whatsapp_session",
    keywords=["urgent", "asap", "invoice", "payment", "help", "client"]
)
watcher.run()
```

---

## Skill: `watch_linkedin`
**Description:** Monitor LinkedIn notifications and connection requests, write to `/Needs_Action`.
**Module:** `SilverTier/watchers/linkedin_watcher.py`

```python
from watchers.linkedin_watcher import LinkedInWatcher
watcher = LinkedInWatcher(vault_path="./Vault")
watcher.run()
```

**Env vars required:** `LINKEDIN_ACCESS_TOKEN`

---

## Skill: `human_approval`
**Description:** Prompt human for approval before any sensitive action. Blocks execution until `/Approved` or `/Rejected`.
**Module:** `SilverTier/reasoning/approval.py`

```python
from reasoning.approval import ApprovalGate
gate = ApprovalGate(vault_path="./Vault")

approved = gate.request_approval(
    action_type="send_email",
    description="Reply to ACME Corp invoice request",
    details={"to": "client@acme.com", "amount": "$1,200"},
    timeout_hours=24
)

if approved:
    # Execute action
    pass
```

---

## Skill: `schedule_task`
**Description:** Register watchers and orchestrator as Windows Task Scheduler jobs to run on login and periodically.
**Module:** `SilverTier/scheduler/setup_tasks.ps1`

```powershell
# Register all scheduled tasks
powershell -ExecutionPolicy Bypass -File SilverTier/scheduler/setup_tasks.ps1

# Tasks created:
# - AI-Employee-Orchestrator    (on login, every 5 min)
# - AI-Employee-Gmail-Watcher   (every 2 min)
# - AI-Employee-Finance-Watcher (every 30 min)
# - AI-Employee-LinkedIn        (daily at 9am)
```

---

## MCP Server Endpoints Reference

### Email MCP Server (port 8001)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/send-email` | POST | Send real email via Gmail SMTP |
| `/draft-email` | POST | Save draft to Vault/Drafts/ |
| `/search-emails` | GET | Search sent/received emails |
| `/health` | GET | Server health check |

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `GROQ_MODEL` | ❌ | Default: `llama-3.3-70b-versatile` |
| `VAULT_PATH` | ✅ | Absolute path to Obsidian vault |
| `GMAIL_EMAIL` | ✅ Email | Your Gmail address |
| `GMAIL_APP_PASSWORD` | ✅ Email | Gmail App Password (16 chars) |
| `LINKEDIN_ACCESS_TOKEN` | ✅ LinkedIn | OAuth2 access token |
| `LINKEDIN_CLIENT_ID` | ✅ LinkedIn | App client ID |
| `LINKEDIN_CLIENT_SECRET` | ✅ LinkedIn | App client secret |
| `EMAIL_MCP_URL` | ❌ | Default: `http://localhost:8001` |
| `REASONING_MAX_TOKENS` | ❌ | Default: 4096 |
