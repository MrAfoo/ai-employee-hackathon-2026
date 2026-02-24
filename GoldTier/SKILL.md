# 🥇 Gold Tier Agent Skills

> Claude Code reads this file to discover all available skills in the Gold Tier.
> Gold Tier is the Autonomous Employee — cross-domain integration, Odoo accounting,
> social media, multi-MCP orchestration, weekly CEO briefing, and error recovery.

---

## Skill: `odoo_get_pl`
**Description:** Fetch Profit & Loss data from Odoo Community via JSON-RPC API.
**Module:** `GoldTier/mcp_servers/odoo_mcp_server.py`
**Endpoint:** `POST http://localhost:8004/pl-report`

```python
import httpx
response = httpx.post("http://localhost:8004/pl-report", json={
    "date_from": "2026-01-01",
    "date_to": "2026-01-31"
})
pl_data = response.json()
```

**Start server:**
```bash
python GoldTier/mcp_servers/odoo_mcp_server.py
```

**Env vars required:** `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`

---

## Skill: `odoo_create_invoice`
**Description:** Create a customer invoice in Odoo.
**Module:** `GoldTier/mcp_servers/odoo_mcp_server.py`
**Endpoint:** `POST http://localhost:8004/create-invoice`

```python
response = httpx.post("http://localhost:8004/create-invoice", json={
    "partner_name": "ACME Corp",
    "amount": 1200.00,
    "description": "Project Alpha Milestone 2",
    "currency": "USD"
})
```

---

## Skill: `odoo_log_transaction`
**Description:** Log a financial transaction to Odoo from a vault finance note.
**Module:** `GoldTier/mcp_servers/odoo_mcp_server.py`
**Endpoint:** `POST http://localhost:8004/log-transaction`

```python
response = httpx.post("http://localhost:8004/log-transaction", json={
    "date": "2026-02-22",
    "description": "Client Payment - ACME Corp",
    "amount": 1200.00,
    "type": "CREDIT"
})
```

---

## Skill: `post_social`
**Description:** Post updates to Facebook and/or LinkedIn simultaneously via Social Media MCP server.
**Module:** `GoldTier/mcp_servers/social_media_mcp_server.py`
**Endpoint:** `POST http://localhost:8005/post`

```python
response = httpx.post("http://localhost:8005/post", json={
    "message": "Excited to announce our Q1 results! 🚀",
    "platforms": ["facebook", "linkedin"],
    "require_approval": True
})
```

**Start server:**
```bash
python GoldTier/mcp_servers/social_media_mcp_server.py
```

**Env vars required:** `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN`, `LINKEDIN_ACCESS_TOKEN`

---

## Skill: `multi_mcp_dispatch`
**Description:** Route Claude tool-calls to the correct MCP server based on action type, with retry logic and audit logging.
**Module:** `GoldTier/orchestrator/multi_mcp_orchestrator.py`

```python
from orchestrator.multi_mcp_orchestrator import MultiMCPOrchestrator
orch = MultiMCPOrchestrator(vault_path="./Vault")

result = orch.dispatch(
    action_type="send_email",   # or: post_linkedin, post_facebook, odoo_invoice, odoo_log
    payload={"to": "client@example.com", "subject": "Invoice", "body": "..."}
)
```

**Supported action types:**
| Action | Routes to |
|--------|-----------|
| `send_email` | Email MCP (port 8001) |
| `post_linkedin` | LinkedIn integration |
| `post_facebook` | Social MCP (port 8005) |
| `odoo_invoice` | Odoo MCP (port 8004) |
| `odoo_log` | Odoo MCP (port 8004) |

---

## Skill: `ralph_wiggum_autonomous`
**Description:** Autonomous multi-step task completion loop. Claude iterates with full tool access until the task is done or max iterations reached.
**Module:** `GoldTier/orchestrator/ralph_wiggum_loop.py`

```bash
python GoldTier/orchestrator/ralph_wiggum_loop.py \
  --task "Process all pending invoices in Needs_Action, create Odoo entries, send confirmations" \
  --max-iterations 15 \
  --completion-check "Done folder contains APPROVED files"
```

**How it works:**
1. Orchestrator creates state file with task prompt
2. Claude works on task using MCP tools
3. Claude tries to exit → Stop hook intercepts
4. Hook checks: Is task complete? (file in `/Done` OR `<promise>TASK_COMPLETE</promise>`)
5. NO → re-inject prompt with previous output context
6. YES → allow exit

---

## Skill: `weekly_ceo_briefing`
**Description:** Generate a weekly CEO briefing combining Odoo P&L + vault activity + error summary. Saves to `Vault/CEO_Briefing_YYYY-WW.md`.
**Module:** `GoldTier/briefing/ceo_briefing.py`

```bash
# Generate this week's briefing
python GoldTier/briefing/ceo_briefing.py

# Generate for specific week
python GoldTier/briefing/ceo_briefing.py --week 2026-W08
```

**Output sections:**
- 💼 Executive Summary
- 💰 Financial Overview (from Odoo)
- 📊 Agent Activity Summary
- 📬 Inbox Summary
- ⚠️ Errors & Issues
- 🎯 Next Week's Priorities
- ✅ Action Items

---

## Skill: `audit_log`
**Description:** Write structured JSONL audit entries for every agent action. Query and summarise audit history.
**Module:** `GoldTier/audit/audit_logger.py`

```python
from audit.audit_logger import AuditLogger, with_recovery

logger = AuditLogger(log_path="./GoldTier/logs/audit.jsonl")

# Log an event
logger.log(
    event_type="email_sent",
    agent="orchestrator",
    details={"to": "client@example.com", "subject": "Invoice"}
)

# Use decorator for automatic error recovery
@with_recovery(max_retries=3, backoff=2.0)
def send_important_email():
    pass
```

**Error categories & recovery:**
| Category | Examples | Recovery |
|----------|----------|----------|
| Transient | Network timeout, API rate limit | Exponential backoff retry |
| Authentication | Token expired | Alert human, pause operations |
| Logic | LLM misinterprets task | Human review queue |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Orchestrator crash, disk full | Watchdog + auto-restart |

---

## Skill: `error_recovery`
**Description:** Wrap any function with automatic error recovery — retry, backoff, quarantine, and human escalation.
**Module:** `BronzeTier/error_recovery.py`

```python
from error_recovery import ErrorRecovery, ErrorCategory

recovery = ErrorRecovery(vault_path="./Vault")

# Classify and handle an error
recovery.handle_error(
    error=exception,
    category=ErrorCategory.TRANSIENT,
    context={"action": "send_email", "file": "APPROVAL_xyz.md"}
)
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `VAULT_PATH` | ✅ | Absolute path to Obsidian vault |
| `ODOO_URL` | ✅ Odoo | e.g. `http://localhost:8069` |
| `ODOO_DB` | ✅ Odoo | Odoo database name |
| `ODOO_USER` | ✅ Odoo | Odoo admin username |
| `ODOO_PASSWORD` | ✅ Odoo | Odoo admin password |
| `FACEBOOK_PAGE_ID` | ✅ FB | Facebook Page ID |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | ✅ FB | Page access token |
| `LINKEDIN_ACCESS_TOKEN` | ✅ LinkedIn | OAuth2 access token |
