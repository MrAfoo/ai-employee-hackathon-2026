# 🥈 Silver Tier — Functional Assistant

Multi-source watchers, LinkedIn auto-posting, MCP email server, reasoning loop.

## Quick Start

```powershell
# Install
pip install -r requirements.txt

# Set up credentials
Copy-Item .env.example .env
# Fill in: GROQ_API_KEY, LINKEDIN_ACCESS_TOKEN, GMAIL_EMAIL, GMAIL_APP_PASSWORD

# Start Email MCP server (port 8001)
python mcp_servers/email_mcp_server.py

# Run reasoning loop manually
python reasoning/reasoning_loop.py --vault-path ../Vault

# Set up Windows Task Scheduler (run once)
.\scheduler\setup_tasks.ps1
```

## MCP Servers

### Email MCP Server (`mcp_servers/email_mcp_server.py`)
Runs on `http://localhost:8001`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/send-email` | POST | Send real Gmail via SMTP |
| `/draft-email` | POST | Save draft to `Vault/Drafts/` |
| `/health` | GET | Health check |

### LinkedIn MCP Server (`mcp_servers/linkedin_mcp_server.py`)
Runs on `http://localhost:8002`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/post` | POST | Post update to LinkedIn |
| `/health` | GET | Health check |

## Credentials Needed

| Credential | Required | How to Get |
|-----------|----------|-----------|
| `GROQ_API_KEY` | ✅ Yes | [console.groq.com](https://console.groq.com) — free |
| `GMAIL_EMAIL` | For email sending | Your Gmail address |
| `GMAIL_APP_PASSWORD` | For email sending | Google Account → Security → App Passwords |
| `LINKEDIN_ACCESS_TOKEN` | For LinkedIn posting | LinkedIn Developer Portal |
| `WHATSAPP_API_TOKEN` | For WhatsApp API | Meta Developer Portal |
