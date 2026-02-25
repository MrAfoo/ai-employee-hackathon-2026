"""
Orchestrator.py – Master Python Orchestrator (Bronze Tier)

Tech Stack:
  - Knowledge Base  : Obsidian vault (local Markdown files)
  - External I/O    : MCP Servers (Gmail, WhatsApp, Banking)
  - Computer Use    : Playwright (payment portals, websites)
  - Automation Glue : This file – handles timing, folder watching, error recovery

Architecture: Perception → Reasoning → Action
  1. Watchers  detect changes → write .md to /Needs_Action
  2. Orchestrator detects /Needs_Action files → calls Groq to reason
  3. Groq writes Plan.md → Orchestrator routes to MCP servers or HITL
  4. HITL: sensitive actions wait in /Pending_Approval until human approves
"""

import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# ── Ensure BronzeTier/ is in path regardless of working directory ──────────────
_BRONZE_DIR = Path(__file__).resolve().parent
if str(_BRONZE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRONZE_DIR))

from dotenv import load_dotenv
# Load .env from BronzeTier/ directory explicitly
load_dotenv(dotenv_path=_BRONZE_DIR / ".env")
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from error_recovery import (
    ErrorCategory,
    ErrorRecovery,
    QuarantineManager,
    with_error_recovery,
)
from watchers.base_watcher import BaseWatcher
from watchers.filesystem_watcher import DropFolderHandler
from watchers.finance_watcher import FinanceWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("orchestrator.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("Orchestrator")

# ── Config ─────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.getenv("VAULT_PATH", "./Vault"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GMAIL_CREDENTIALS = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")
WHATSAPP_SESSION = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session")
FINANCE_DROP = os.getenv("FINANCE_DROP_PATH", str(VAULT_PATH / "Finance_Drop"))
POLL_INTERVAL = int(os.getenv("WATCHER_POLL_INTERVAL", "60"))
APPROVAL_THRESHOLD = float(os.getenv("APPROVAL_THRESHOLD_AMOUNT", "500"))


class NeedsActionHandler(FileSystemEventHandler):
    """
    Watches /Needs_Action folder. When a new .md file appears,
    triggers the reasoning loop to generate Plan.md.
    """

    def __init__(self, orchestrator: "Orchestrator"):
        self.orchestrator = orchestrator
        self._processing: set = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix == ".md" and path not in self._processing:
            self._processing.add(path)
            log.info("New Needs_Action file detected: %s", path.name)
            threading.Thread(
                target=self._handle,
                args=(path,),
                daemon=True,
                name=f"handle-{path.stem}",
            ).start()

    def _handle(self, path: Path):
        try:
            self.orchestrator.process_needs_action_file(path)
        finally:
            self._processing.discard(path)


class Orchestrator:
    """
    Master orchestrator. Manages:
      - Watcher threads (Gmail, WhatsApp, Filesystem, Finance)
      - /Needs_Action folder monitoring
      - Groq reasoning loop → Plan.md generation
      - HITL approval routing
      - Error recovery and health checks
    """

    def __init__(self):
        self.vault = VAULT_PATH
        self.needs_action = self.vault / "Needs_Action"
        self.pending_approval = self.vault / "Pending_Approval"
        self.approved = self.vault / "Approved"
        self.rejected = self.vault / "Rejected"
        self.done = self.vault / "Done"
        self.accounting = self.vault / "Accounting"

        # Ensure all folders exist
        for folder in [
            self.needs_action, self.pending_approval,
            self.approved, self.rejected, self.done, self.accounting,
            self.vault / "Inbox",
        ]:
            folder.mkdir(parents=True, exist_ok=True)

        self.recovery = ErrorRecovery()
        self.quarantine = QuarantineManager(self.vault / "Quarantine")
        self._shutdown = threading.Event()
        self._watcher_threads: list[threading.Thread] = []
        self._observers: list[Observer] = []

        # Groq client (lazy import to allow running without groq installed)
        self._groq = None

    # ── Groq Client ────────────────────────────────────────────────────────────
    @property
    def groq(self):
        if self._groq is None:
            from groq import Groq
            self._groq = Groq(api_key=GROQ_API_KEY)
        return self._groq

    # ── Watcher Management ─────────────────────────────────────────────────────
    def _start_watcher_thread(self, watcher: BaseWatcher, name: str):
        """Start a watcher in a daemon thread with auto-restart on crash."""
        def _run():
            while not self._shutdown.is_set():
                try:
                    log.info("Starting watcher: %s", name)
                    watcher.run()
                except Exception as exc:
                    self.recovery.record_error(ErrorCategory.SYSTEM, str(exc), name)
                    log.error("Watcher %s crashed: %s — restarting in 30s", name, exc)
                    time.sleep(30)

        t = threading.Thread(target=_run, daemon=True, name=name)
        t.start()
        self._watcher_threads.append(t)
        return t

    def start_watchers(self):
        """Initialise and start all watchers."""
        # Gmail
        if GMAIL_CREDENTIALS and Path(GMAIL_CREDENTIALS).exists():
            try:
                gmail = GmailWatcher(str(self.vault), GMAIL_CREDENTIALS)
                self._start_watcher_thread(gmail, "GmailWatcher")
            except Exception as e:
                log.warning("Gmail watcher failed to start: %s", e)
        else:
            log.warning("Gmail credentials not found — skipping GmailWatcher")

        # WhatsApp
        try:
            wa = WhatsAppWatcher(str(self.vault), WHATSAPP_SESSION)
            self._start_watcher_thread(wa, "WhatsAppWatcher")
        except Exception as e:
            log.warning("WhatsApp watcher failed to start: %s", e)

        # Finance / CSV drop
        try:
            finance = FinanceWatcher(str(self.vault), FINANCE_DROP)
            self._start_watcher_thread(finance, "FinanceWatcher")
        except Exception as e:
            log.warning("Finance watcher failed to start: %s", e)

        # Filesystem drop folder (watchdog-based)
        drop_handler = DropFolderHandler(str(self.vault))
        observer = Observer()
        drop_path = self.vault / "Drop"
        drop_path.mkdir(parents=True, exist_ok=True)
        observer.schedule(drop_handler, str(drop_path), recursive=False)
        observer.start()
        self._observers.append(observer)
        log.info("FilesystemWatcher active on: %s", drop_path)

    def start_needs_action_monitor(self):
        """Watch /Needs_Action folder for new .md files."""
        handler = NeedsActionHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.needs_action), recursive=False)
        observer.start()
        self._observers.append(observer)
        log.info("NeedsAction monitor active on: %s", self.needs_action)

    def start_hitl_monitor(self):
        """Poll /Approved and /Rejected folders every 10s for human decisions."""
        def _poll():
            while not self._shutdown.is_set():
                self._process_approved()
                self._process_rejected()
                time.sleep(10)

        t = threading.Thread(target=_poll, daemon=True, name="HITLMonitor")
        t.start()
        self._watcher_threads.append(t)

    # ── Reasoning Loop ─────────────────────────────────────────────────────────
    @with_error_recovery(retries=3, backoff=2.0, category=ErrorCategory.TRANSIENT)
    def process_needs_action_file(self, path: Path):
        """
        Read a Needs_Action .md file, send to Groq, write Plan.md,
        and route sensitive actions to HITL.
        """
        content = path.read_text(encoding="utf-8")
        log.info("Processing: %s (%d chars)", path.name, len(content))

        # Check for data integrity
        if not content.strip():
            self.quarantine.quarantine(path, "Empty file")
            return

        # Build context from handbook (Rules of Engagement)
        handbook_path = self.vault / "Company_Handbook.md"
        handbook = handbook_path.read_text(encoding="utf-8") if handbook_path.exists() else ""

        prompt = f"""You are an autonomous AI executive assistant.

RULES OF ENGAGEMENT (from Company Handbook):
{handbook[:2000]}

NEW ITEM REQUIRING ATTENTION:
File: {path.name}
---
{content}
---

Today: {datetime.now().strftime('%Y-%m-%d %A %H:%M')}

Your response MUST be a JSON object with these fields:
{{
  "summary": "one-line summary of the item",
  "category": "email|whatsapp|finance|file|other",
  "urgency": "high|medium|low",
  "requires_approval": true/false,
  "approval_reason": "why approval is needed (if applicable)",
  "amount": 0.0,
  "actions": [
    {{"action": "reply_email|send_whatsapp|log_transaction|move_to_done|other",
      "description": "what to do",
      "mcp_server": "email|whatsapp|browser|filesystem"}}
  ],
  "plan_entry": "markdown checkbox entry for Plan.md"
}}

Flag requires_approval=true if: payment > {APPROVAL_THRESHOLD}, sending external comms, or irreversible action.
"""

        response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            self.quarantine.quarantine(path, f"Groq returned non-JSON: {raw[:200]}")
            self.recovery.record_error(ErrorCategory.LOGIC, "Non-JSON Groq response", path.name)
            return

        # Write to Plan.md
        self._update_plan(plan, path)

        # Route: HITL or auto-process
        if plan.get("requires_approval"):
            self._create_approval_request(path, plan)
        else:
            self._auto_process(path, plan)

        # Always refresh dashboard after any processing
        self._update_dashboard()

    def _update_plan(self, plan: dict, source_path: Path):
        """Append a checkbox entry to Plan.md."""
        plan_path = self.vault / "Plan.md"
        entry = plan.get("plan_entry", f"- [ ] Process {source_path.name}")
        urgency = plan.get("urgency", "low")
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency, "⚪")

        today = datetime.now().strftime("%Y-%m-%d")
        header = f"\n## {emoji} {today} — {plan.get('summary', source_path.name)}\n"

        with plan_path.open("a", encoding="utf-8") as f:
            f.write(header)
            f.write(entry + "\n")

        log.info("Plan.md updated with: %s", plan.get("summary", ""))

    def _create_approval_request(self, source_path: Path, plan: dict):
        """Write an approval request file to /Pending_Approval."""
        now = datetime.now()
        safe_name = source_path.stem.replace(" ", "_")
        approval_path = self.pending_approval / f"APPROVAL_REQUIRED_{safe_name}_{now.strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
type: approval_request
source_file: {source_path.name}
summary: {plan.get('summary', '')}
urgency: {plan.get('urgency', 'medium')}
amount: {plan.get('amount', 0.0)}
reason: {plan.get('approval_reason', 'Sensitive action requires human approval')}
created: {now.isoformat()}
expires: {now.replace(hour=23, minute=59).isoformat()}
status: pending
actions: {json.dumps(plan.get('actions', []), indent=2)}
---

## Summary
{plan.get('summary', '')}

## Why Approval Is Needed
{plan.get('approval_reason', 'This action requires human approval.')}

## Planned Actions
{chr(10).join(f"- {a.get('description', '')}" for a in plan.get('actions', []))}

## Amount Involved
${plan.get('amount', 0.0):.2f}

---
## ✅ To Approve
Move this file to `/Approved` folder.

## ❌ To Reject
Move this file to `/Rejected` folder.
"""
        approval_path.write_text(content, encoding="utf-8")
        log.info("Approval request created: %s", approval_path.name)

    def _auto_process(self, source_path: Path, plan: dict):
        """Log auto-processed actions and move source to /Done."""
        log.info(
            "Auto-processing '%s': %d action(s)",
            plan.get("summary", ""),
            len(plan.get("actions", [])),
        )
        for action in plan.get("actions", []):
            log.info("  → [%s] %s", action.get("mcp_server", "?"), action.get("description", ""))
            # MCP server calls would be dispatched here in Silver/Gold/Platinum tiers

        # Move processed file to /Done
        done_path = self.done / source_path.name
        source_path.rename(done_path)
        log.info("Moved to Done: %s", done_path.name)

    # ── HITL Processing ────────────────────────────────────────────────────────
    def _update_file_status(self, filepath: Path, new_status: str) -> Path:
        """Rewrite the status: field in frontmatter before archiving."""
        try:
            content = filepath.read_text(encoding="utf-8")
            import re
            content = re.sub(
                r'^(status:\s*).*$', f'\\g<1>{new_status}',
                content, count=1, flags=re.MULTILINE
            )
            filepath.write_text(content, encoding="utf-8")
        except Exception as e:
            log.warning("Could not update status in %s: %s", filepath.name, e)
        return filepath

    def _process_approved(self):
        for f in self.approved.glob("*.md"):
            if f.name == ".gitkeep":
                continue
            log.info("APPROVED: %s — executing actions via MCP", f.name)
            self._update_file_status(f, "approved")
            # Dispatch to Silver/Gold MCP email server if available
            try:
                self._dispatch_mcp_email(f)
            except Exception as e:
                log.warning("MCP dispatch skipped: %s", e)
            done_path = self.done / f"APPROVED_{f.name}"
            f.rename(done_path)
            log.info("✅ Moved to Done: %s", done_path.name)
            self._update_dashboard()

    def _process_rejected(self):
        for f in self.rejected.glob("*.md"):
            if f.name == ".gitkeep":
                continue
            if not (f.name.startswith("REJECTED_") or f.name.startswith("FAILED_")):
                log.info("REJECTED: %s — archiving", f.name)
                self._update_file_status(f, "rejected")
                done_path = self.done / f"REJECTED_{f.name}"
                f.rename(done_path)
                log.info("❌ Archived rejected: %s", done_path.name)
                self._update_dashboard()

    def _update_dashboard(self):
        """Rewrite Dashboard.md with current live stats from vault folders."""
        import re
        dashboard_path = self.vault / "Dashboard.md"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Count items in each folder
        needs_action_files  = [f for f in self.needs_action.glob("*.md")    if f.name != ".gitkeep"]
        pending_files       = [f for f in self.pending_approval.glob("*.md") if f.name != ".gitkeep"]
        done_files          = [f for f in self.done.glob("*.md")             if f.name != ".gitkeep"]

        # Build Needs Action table rows
        na_rows = "\n".join(
            f"| {f.stem[:50]} | 🔴 | {datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')} |"
            for f in sorted(needs_action_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        ) or "| — | — | — |"

        # Build Pending Approval table rows
        pa_rows = "\n".join(
            f"| {f.stem[:50]} | — | pending |"
            for f in sorted(pending_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        ) or "| — | — | — |"

        # Build recent Done rows
        done_rows = "\n".join(
            f"| {f.stem[:50]} | {'✅ approved' if f.name.startswith('APPROVED') else '❌ rejected' if f.name.startswith('REJECTED') else '✔ processed'} |"
            for f in sorted(done_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        ) or "| — | — |"

        # Read latest bank balance from Accounting
        balance_line = "—"
        acct_dir = self.vault / "Accounting"
        acct_files = sorted(acct_dir.glob("*.md"), reverse=True)
        if acct_files:
            acct_text = acct_files[0].read_text(encoding="utf-8")
            match = re.search(r"\|\s*Current Balance.*?\|\s*([₨$€£\d,.\s]+)\|", acct_text)
            if match:
                balance_line = match.group(1).strip()

        # System health
        thread_count = sum(1 for t in self._watcher_threads if t.is_alive())
        health_emoji = "🟢" if thread_count > 0 else "🔴"

        dashboard = f"""# 🤖 AI Employee Dashboard
> **Last updated:** {now} (auto-updated by Orchestrator)

---

## 💰 Bank Balance
| Account | Balance | Source |
|---------|---------|--------|
| Business Checking | {balance_line} | Accounting/Current_Month |

---

## 📬 Inbox Summary
| Folder | Count |
|--------|-------|
| 🔴 Needs Action | {len(needs_action_files)} |
| ⏳ Pending Approval | {len(pending_files)} |
| ✅ Done (total) | {len(done_files)} |

---

## 🔴 Needs Action (latest 5)
| File | Urgency | Detected |
|------|---------|----------|
{na_rows}

---

## ⏳ Pending Your Approval (latest 5)
| File | Amount | Status |
|------|--------|--------|
{pa_rows}

---

## ✅ Recently Completed (latest 5)
| File | Outcome |
|------|---------|
{done_rows}

---

## 🏥 System Health
| Component | Status |
|-----------|--------|
| Orchestrator | {health_emoji} Running ({thread_count} watcher threads) |
| Gmail Watcher | {'🟢 Active' if Path(GMAIL_CREDENTIALS).exists() else '🟡 No credentials'} |
| WhatsApp Watcher | 🟡 Read-only (Playwright) |
| Finance Watcher | 🟢 Active |
| Groq API | 🟢 {GROQ_MODEL} |

---
*Single writer: Local Orchestrator | Vault: {self.vault.resolve()}*
"""
        dashboard_path.write_text(dashboard, encoding="utf-8")
        log.info("Dashboard.md updated at %s", now)

    def _dispatch_mcp_email(self, approval_file: Path):
        """Try to dispatch approved email action to Silver Tier MCP server."""
        import json, re
        content = approval_file.read_text(encoding="utf-8")
        # Extract actions JSON from frontmatter
        match = re.search(r'^actions:\s*(\[.*?\])\s*$', content, re.MULTILINE | re.DOTALL)
        if not match:
            return
        actions = json.loads(match.group(1))
        for action in actions:
            if action.get("mcp_server") == "email":
                mcp_url = os.getenv("EMAIL_MCP_URL", "http://localhost:8001")
                import requests
                try:
                    resp = requests.post(
                        f"{mcp_url}/send",
                        json=action,
                        timeout=10,
                    )
                    log.info("MCP email server response: %s", resp.status_code)
                except requests.exceptions.ConnectionError:
                    log.info("Email MCP server not running — action logged only")

    # ── Health Check ───────────────────────────────────────────────────────────
    def health_check(self) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "vault_exists": self.vault.exists(),
            "needs_action_count": len(list(self.needs_action.glob("*.md"))),
            "pending_approval_count": len(list(self.pending_approval.glob("*.md"))),
            "watcher_threads": sum(1 for t in self._watcher_threads if t.is_alive()),
            "observers": sum(1 for o in self._observers if o.is_alive()),
            "recent_errors": self.recovery.recent_errors(limit=5),
        }

    # ── Shutdown ───────────────────────────────────────────────────────────────
    def shutdown(self):
        log.info("Orchestrator shutting down gracefully...")
        self._shutdown.set()
        for observer in self._observers:
            observer.stop()
            observer.join(timeout=5)
        log.info("Shutdown complete.")

    # ── Main Run ───────────────────────────────────────────────────────────────
    def run(self):
        log.info("=" * 60)
        log.info("AI Employee Orchestrator – Bronze Tier")
        log.info("Vault: %s", self.vault.resolve())
        log.info("Model: %s", GROQ_MODEL)
        log.info("=" * 60)

        # Register shutdown handlers
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())

        self.start_watchers()
        self.start_needs_action_monitor()
        self.start_hitl_monitor()

        log.info("All systems active. Watching for changes...")

        # Health check loop
        while not self._shutdown.is_set():
            health = self.health_check()
            log.info(
                "Health: needs_action=%d pending_approval=%d threads=%d",
                health["needs_action_count"],
                health["pending_approval_count"],
                health["watcher_threads"],
            )
            self._shutdown.wait(timeout=300)  # Log health every 5 minutes


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
