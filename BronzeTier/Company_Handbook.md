# Company Handbook

## Mission
We build autonomous AI agent systems that scale from personal productivity to full business operations.

## Tiers of Operation

### 🥉 Bronze – Foundation
File-system inbox, Gmail watcher, Obsidian vault integration, modular Agent Skills.

### 🥈 Silver – Functional Assistant
Multi-source watchers (Gmail, WhatsApp, LinkedIn), MCP server for outbound actions, human-in-the-loop approval, Claude reasoning loop.

### 🥇 Gold – Autonomous Employee
Full cross-domain integration, Odoo accounting, social media orchestration, weekly CEO briefing, error recovery, Ralph Wiggum autonomous loop.

## Folder Conventions
| Folder | Purpose |
|--------|---------|
| `/Inbox` | Raw notes written by watchers |
| `/Needs_Action` | Items flagged for human review |
| `/Done` | Archived completed items |

## Agent Skill Interface
All AI functionality is implemented as modular **Agent Skills**:
- Each skill is a Python class with `run()` and `describe()` methods.
- Skills are registered in `skills/registry.py`.
- Skills can be chained by the reasoning loop.

## Contact & Escalation
- Urgent items: escalate via email MCP server.
- Weekly briefing: auto-generated every Monday at 08:00.
