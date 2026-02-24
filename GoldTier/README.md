# 🥇 Gold Tier — Autonomous Employee

Cross-domain integration, Odoo accounting, social media, CEO briefing, Ralph Wiggum loop.

## Quick Start

```powershell
# Install
pip install -r requirements.txt

# Set up credentials
Copy-Item .env.example .env

# Run multi-MCP orchestrator
python orchestrator/multi_mcp_orchestrator.py

# Generate CEO briefing
python briefing/ceo_briefing.py --vault-path ../Vault

# Start Ralph Wiggum autonomous loop
python orchestrator/ralph_wiggum_loop.py \
  --task "Process all Needs_Action files" \
  --max-iterations 10
```

## Components

| Component | File | Description |
|-----------|------|-------------|
| Multi-MCP Orchestrator | `orchestrator/multi_mcp_orchestrator.py` | Routes Claude tool-calls to MCP servers |
| Ralph Wiggum Loop | `orchestrator/ralph_wiggum_loop.py` | Autonomous multi-step task completion |
| Odoo MCP Server | `mcp_servers/odoo_mcp_server.py` | Odoo accounting via JSON-RPC |
| Social Media MCP | `mcp_servers/social_media_mcp_server.py` | Facebook/LinkedIn posting |
| CEO Briefing | `briefing/ceo_briefing.py` | Weekly Markdown briefing |
| Audit Logger | `audit/audit_logger.py` | JSONL structured audit log |

## Ralph Wiggum Loop

The autonomous multi-step task completion loop:

```
1. Orchestrator creates task state file
2. Groq works on task using tools
3. Groq tries to complete
4. Loop checks: is task done?
   YES → exit (complete)
   NO  → re-inject prompt, continue
5. Repeat until complete or max iterations
```

## Credentials Needed

| Credential | Required | How to Get |
|-----------|----------|-----------|
| `GROQ_API_KEY` | ✅ Yes | [console.groq.com](https://console.groq.com) — free |
| `ODOO_URL` | For accounting | Install Odoo Community locally |
| `ODOO_DB` | For accounting | Your Odoo database name |
| `ODOO_USER` | For accounting | Odoo admin username |
| `ODOO_PASSWORD` | For accounting | Odoo admin password |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | For Facebook | Meta Developer Portal |
| `LINKEDIN_ACCESS_TOKEN` | For LinkedIn | LinkedIn Developer Portal |
