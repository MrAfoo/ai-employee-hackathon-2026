# 🤖 AI Employee — Agent Skills Index

> This file is the master index of all Agent Skills across all tiers.
> Claude Code reads this file first to discover what capabilities are available.
> Each tier has its own `SKILL.md` with full documentation and code examples.

---

## Quick Reference: All Skills

| Skill | Tier | Module | Description |
|-------|------|--------|-------------|
| `read_vault` | 🥉 Bronze | `skills/vault_skill.py` | Read Markdown files from Obsidian vault |
| `write_vault` | 🥉 Bronze | `skills/vault_skill.py` | Write/update Markdown files in vault |
| `move_note` | 🥉 Bronze | `skills/vault_skill.py` | Move notes between vault folders |
| `list_vault` | 🥉 Bronze | `skills/vault_skill.py` | List files in a vault folder |
| `update_dashboard` | 🥉 Bronze | `Orchestrator.py` | Refresh Dashboard.md with live counts |
| `watch_gmail` | 🥉 Bronze | `watchers/gmail_watcher.py` | Poll Gmail → Needs_Action files |
| `watch_filesystem` | 🥉 Bronze | `watchers/filesystem_watcher.py` | Monitor drop folder → Needs_Action |
| `watch_whatsapp` | 🥉 Bronze | `watchers/whatsapp_watcher.py` | Playwright WhatsApp Web (read-only) |
| `watch_finance` | 🥉 Bronze | `watchers/finance_watcher.py` | CSV bank statements → Accounting |
| `reason_about_notes` | 🥉 Bronze | `Orchestrator.py` | Groq LLM reasoning on vault notes |
| `hitl_approve` | 🥉 Bronze | `Orchestrator.py` | Create HITL approval request |
| `ralph_wiggum_loop` | 🥉 Bronze | `watchers/ralph_wiggum_hook.py` | Stop hook — iterate until task done |
| `run_orchestrator` | 🥉 Bronze | `Orchestrator.py` | Start full Bronze Tier system |
| `reasoning_loop` | 🥈 Silver | `reasoning/reasoning_loop.py` | Generate Plan.md from all vault notes |
| `send_email` | 🥈 Silver | `mcp_servers/email_mcp_server.py` | Send real email via Gmail SMTP |
| `draft_email` | 🥈 Silver | `mcp_servers/email_mcp_server.py` | Save email draft to Vault/Drafts/ |
| `post_linkedin` | 🥈 Silver | `linkedin_integration.py` | Draft + publish LinkedIn post |
| `watch_linkedin` | 🥈 Silver | `watchers/linkedin_watcher.py` | Monitor LinkedIn notifications |
| `human_approval` | 🥈 Silver | `reasoning/approval.py` | Block execution until human approves |
| `schedule_task` | 🥈 Silver | `scheduler/setup_tasks.ps1` | Register Windows Task Scheduler jobs |
| `odoo_get_pl` | 🥇 Gold | `mcp_servers/odoo_mcp_server.py` | Fetch P&L from Odoo |
| `odoo_create_invoice` | 🥇 Gold | `mcp_servers/odoo_mcp_server.py` | Create invoice in Odoo |
| `odoo_log_transaction` | 🥇 Gold | `mcp_servers/odoo_mcp_server.py` | Log transaction to Odoo |
| `post_social` | 🥇 Gold | `mcp_servers/social_media_mcp_server.py` | Post to Facebook + LinkedIn |
| `multi_mcp_dispatch` | 🥇 Gold | `orchestrator/multi_mcp_orchestrator.py` | Route actions to correct MCP server |
| `ralph_wiggum_autonomous` | 🥇 Gold | `orchestrator/ralph_wiggum_loop.py` | Autonomous multi-step task loop |
| `weekly_ceo_briefing` | 🥇 Gold | `briefing/ceo_briefing.py` | Generate weekly CEO briefing |
| `audit_log` | 🥇 Gold | `audit/audit_logger.py` | Structured JSONL audit logging |
| `error_recovery` | 🥇 Gold | `BronzeTier/error_recovery.py` | Error classification + recovery |
| `cloud_orchestrate` | 🏆 Platinum | `cloud_orchestrator.py` | Run cloud VM orchestrator |
| `local_agent` | 🏆 Platinum | `local_agent.py` | Run local laptop agent |
| `vault_sync` | 🏆 Platinum | `vault_sync.py` | Git sync vault between cloud + local |
| `claim_task` | 🏆 Platinum | `claim_orchestrator.py` | Atomic task claiming (multi-agent) |
| `health_monitor` | 🏆 Platinum | `health_monitor.py` | Monitor all services, alert on failure |
| `deploy_cloud` | 🏆 Platinum | `deploy_cloud.sh` | One-command Oracle VM deploy |
| `setup_startup_local` | 🏆 Platinum | `setup_startup.ps1` | Windows startup task registration |

---

## Tier Documentation

| Tier | SKILL.md | README.md | .env.example |
|------|----------|-----------|--------------|
| 🥉 Bronze | [BronzeTier/SKILL.md](BronzeTier/SKILL.md) | [BronzeTier/README.md](BronzeTier/README.md) | [BronzeTier/.env.example](BronzeTier/.env.example) |
| 🥈 Silver | [SilverTier/SKILL.md](SilverTier/SKILL.md) | [SilverTier/README.md](SilverTier/README.md) | [SilverTier/.env.example](SilverTier/.env.example) |
| 🥇 Gold | [GoldTier/SKILL.md](GoldTier/SKILL.md) | [GoldTier/README.md](GoldTier/README.md) | [GoldTier/.env.example](GoldTier/.env.example) |
| 🏆 Platinum | [PlatinumTier/SKILL.md](PlatinumTier/SKILL.md) | [PlatinumTier/README.md](PlatinumTier/README.md) | [PlatinumTier/.env.example](PlatinumTier/.env.example) |

---

## HITL Safeguards (Built Into Every Tier)

All sensitive actions across all tiers require human approval:

| Action | Threshold | Approval Method |
|--------|-----------|----------------|
| Email send | Always (first time) | Move to `/Approved` |
| Payment | > $500 | Move to `/Approved` |
| Wire transfer | Always | Move to `/Approved` |
| LinkedIn post | Always | Move to `/Approved` |
| Social media post | Always | Move to `/Approved` |
| Invoice creation | > $1,000 | Move to `/Approved` |
| Odoo transaction | > $500 | Move to `/Approved` |

---

## Credential Requirements Summary

| Credential | Where | How to Get |
|-----------|-------|-----------|
| `GROQ_API_KEY` | All tiers | [console.groq.com](https://console.groq.com) (free) |
| `GMAIL_CREDENTIALS_PATH` | Bronze+ | Google Cloud Console → Gmail API |
| `GMAIL_TOKEN_PATH` | Bronze+ | Auto-generated by `setup_gmail_oauth.py` |
| `LINKEDIN_ACCESS_TOKEN` | Silver+ | LinkedIn Developer Portal |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Gold+ | Meta Developer Portal |
| `ODOO_URL/DB/USER/PASSWORD` | Gold+ | Your Odoo Community install |
| `VAULT_GIT_REMOTE` | Platinum | Your private GitHub repo |
| `CLOUD_VM_IP` | Platinum | Oracle Free VM public IP |

---

## One-Click Start

```powershell
# Start entire system (Bronze + Silver MCP servers):
.\start_all.ps1

# Start with watchdog (auto-restart on crash):
python BronzeTier/watchdog_monitor.py
```

---

## Architecture: Perception → Reasoning → Action

```
📧 Gmail     ┐
📱 WhatsApp  ├─► /Needs_Action ──► Groq Reasoning ──► Plan.md
💰 Finance   ┘         │                                  │
📁 File Drop           │                                  ▼
                       │                         Sensitive? ──► /Pending_Approval
                       │                              │               │
                       │                           NO │           YOU review
                       ▼                              │               │
                  Auto-process                        └──► /Approved or /Rejected
                  → /Done                                        │
                                                                 ▼
                                                    MCP Server executes action
                                                    → Email sent / LinkedIn posted
                                                    → /Done (status: approved)
```
