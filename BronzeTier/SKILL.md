# 🥉 Bronze Tier Agent Skills

> Claude Code reads this file to discover all available skills in the Bronze Tier.
> Invoke any skill by referencing its name and parameters below.

---

## Skill: `read_vault`
**Description:** Read one or more Markdown files from the Obsidian vault.
**Module:** `BronzeTier/skills/vault_skill.py`
**Function:** `VaultSkill.read_note(path)`

```python
# Example invocation
from skills.vault_skill import VaultSkill
vault = VaultSkill(vault_path="./Vault")
content = vault.read_note("Needs_Action/EMAIL_xyz.md")
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | str | ✅ | Relative path from vault root |

**Returns:** `str` — Markdown content of the file

---

## Skill: `write_vault`
**Description:** Write or update a Markdown file in the Obsidian vault.
**Module:** `BronzeTier/skills/vault_skill.py`
**Function:** `VaultSkill.write_note(path, content, overwrite)`

```python
vault.write_note("Plan.md", "# Plan\n- [ ] Reply to client", overwrite=True)
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | str | ✅ | Relative path from vault root |
| `content` | str | ✅ | Markdown content to write |
| `overwrite` | bool | ❌ | Default: True |

---

## Skill: `move_note`
**Description:** Move a note between vault folders (e.g. Needs_Action → Done).
**Module:** `BronzeTier/skills/vault_skill.py`
**Function:** `VaultSkill.move_note(source, destination)`

```python
vault.move_note("Needs_Action/EMAIL_xyz.md", "Done/EMAIL_xyz.md")
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source` | str | ✅ | Source path relative to vault root |
| `destination` | str | ✅ | Destination path relative to vault root |

---

## Skill: `list_vault`
**Description:** List all `.md` files in a vault folder.
**Module:** `BronzeTier/skills/vault_skill.py`
**Function:** `VaultSkill.list_notes(folder)`

```python
files = vault.list_notes("Needs_Action")
# Returns: ["EMAIL_abc.md", "WHATSAPP_urgent.md", ...]
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder` | str | ✅ | Folder name relative to vault root |

**Returns:** `list[str]` — filenames

---

## Skill: `update_dashboard`
**Description:** Refresh `Dashboard.md` with current counts from all vault folders.
**Module:** `BronzeTier/Orchestrator.py`
**Function:** `Orchestrator._update_dashboard()`

```python
from Orchestrator import Orchestrator
orch = Orchestrator(vault_path="./Vault")
orch._update_dashboard()
```

**Triggers automatically:** After every file processed, approved, or rejected.

---

## Skill: `watch_gmail`
**Description:** Poll Gmail for unread important emails and write them to `/Needs_Action`.
**Module:** `BronzeTier/watchers/gmail_watcher.py`
**Function:** `GmailWatcher.run()`

```python
from watchers.gmail_watcher import GmailWatcher
watcher = GmailWatcher(vault_path="./Vault", credentials_path="./credentials.json", token_path="./token.json")
watcher.run()  # Polls every 120 seconds
```

**Env vars required:**
- `GMAIL_CREDENTIALS_PATH`
- `GMAIL_TOKEN_PATH`

---

## Skill: `watch_filesystem`
**Description:** Monitor a drop folder for new files and write metadata notes to `/Needs_Action`.
**Module:** `BronzeTier/watchers/filesystem_watcher.py`
**Function:** `DropFolderHandler` + `Observer`

```python
from watchers.filesystem_watcher import FilesystemWatcher
watcher = FilesystemWatcher(vault_path="./Vault", drop_folder="./Vault/Drop")
watcher.run()
```

---

## Skill: `watch_whatsapp`
**Description:** Monitor WhatsApp Web (Playwright) for keyword-matched messages, write to `/Needs_Action`.
**Module:** `BronzeTier/watchers/whatsapp_watcher.py`
**Function:** `WhatsAppWatcher.run()`

```python
from watchers.whatsapp_watcher import WhatsAppWatcher
watcher = WhatsAppWatcher(vault_path="./Vault", session_path="./whatsapp_session")
# First run: watcher.setup_session()  # Opens browser for QR scan
watcher.run()  # Polls every 30 seconds headless
```

---

## Skill: `watch_finance`
**Description:** Process CSV bank statements dropped in `/Finance_Drop`, log to `/Accounting/Current_Month.md`, flag large transactions to `/Needs_Action`.
**Module:** `BronzeTier/watchers/finance_watcher.py`
**Function:** `FinanceWatcher.run()`

```python
from watchers.finance_watcher import FinanceWatcher
watcher = FinanceWatcher(vault_path="./Vault", drop_folder="./Vault/Finance_Drop")
watcher.run()
```

**Threshold:** Transactions ≥ `APPROVAL_THRESHOLD_AMOUNT` (default $500) are flagged for HITL.

---

## Skill: `reason_about_notes`
**Description:** Send vault notes to Groq LLM for reasoning. Returns structured JSON plan with urgency, actions, and approval requirements.
**Module:** `BronzeTier/Orchestrator.py`
**Function:** `Orchestrator._reason_about_notes(notes_content)`

```python
plan = orch._reason_about_notes("## Email from Client\nPlease send invoice...")
# Returns: {"summary": "...", "urgency": "high", "requires_approval": true, "actions": [...]}
```

**Model:** `llama-3.3-70b-versatile` (via Groq, free tier)
**Env vars required:** `GROQ_API_KEY`, `GROQ_MODEL`

---

## Skill: `hitl_approve`
**Description:** Create a Human-in-the-Loop approval request file in `/Pending_Approval`. Agent will NOT act until you move the file to `/Approved`.
**Module:** `BronzeTier/Orchestrator.py`
**Function:** `Orchestrator._create_approval_request(path, plan)`

```python
orch._create_approval_request(note_path, plan_dict)
# Creates: Vault/Pending_Approval/APPROVAL_REQUIRED_<name>_<timestamp>.md
```

**To approve:** Move file to `Vault/Approved/` → Orchestrator detects within 10s → moves to `Vault/Done/` with `status: approved`
**To reject:** Move file to `Vault/Rejected/` → moves to `Vault/Done/` with `status: rejected`

---

## Skill: `ralph_wiggum_loop`
**Description:** Claude Code Stop hook that keeps Claude iterating until a task is complete. Prevents premature exit.
**Module:** `BronzeTier/watchers/ralph_wiggum_hook.py`

```bash
# Start a Ralph loop
python BronzeTier/watchers/ralph_wiggum_hook.py --start \
  --prompt "Process all files in Needs_Action, move to Done when complete" \
  --max-iterations 10

# Check status
python BronzeTier/watchers/ralph_wiggum_hook.py --status
```

**Completion strategies:**
- Promise-based: Claude outputs `<promise>TASK_COMPLETE</promise>`
- File-based: Task file moves to `/Done`

---

## Skill: `run_orchestrator`
**Description:** Start the full Bronze Tier orchestrator — all watchers + reasoning loop + HITL monitor.
**Module:** `BronzeTier/Orchestrator.py`

```bash
python BronzeTier/Orchestrator.py
# OR via watchdog (auto-restart on crash):
python BronzeTier/watchdog_monitor.py
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key (free at console.groq.com) |
| `GROQ_MODEL` | ❌ | Default: `llama-3.3-70b-versatile` |
| `VAULT_PATH` | ✅ | Absolute path to your Obsidian vault |
| `GMAIL_CREDENTIALS_PATH` | ✅ Gmail | Path to Google OAuth2 credentials.json |
| `GMAIL_TOKEN_PATH` | ✅ Gmail | Path to token.json (auto-generated) |
| `APPROVAL_THRESHOLD_AMOUNT` | ❌ | Default: 500 (USD) |
| `WATCHER_POLL_INTERVAL` | ❌ | Default: 60 seconds |
