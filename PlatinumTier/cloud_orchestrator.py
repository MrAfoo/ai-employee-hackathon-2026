"""
Cloud Orchestrator – runs on Oracle Free VM / AWS EC2.

Responsibilities:
  - Email triage (Gmail watcher)
  - LinkedIn + social media drafts
  - Groq reasoning loop → Plan.md generation
  - Odoo integration (cloud instance)
  - Claims tasks from /Needs_Action via claim-by-move
  - Writes drafts to /Pending_Approval for human approval
  - Always-on (runs 24/7 on the VM)

Does NOT: send WhatsApp, execute payments, click "final send" — those stay Local.
"""
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from claim_orchestrator import ClaimOrchestrator
from vault_sync import VaultSync

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CloudOrchestrator] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("cloud_orchestrator.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("CloudOrchestrator")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./Vault")).resolve()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AGENT_NAME = "cloud"

# ── Groq client ──────────────────────────────────────────────────────────────

_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _ask_groq(prompt: str, max_tokens: int = 2048) -> str:
    """Send a prompt to Groq and return the text response."""
    resp = _groq.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


# ── Task Handlers ─────────────────────────────────────────────────────────────

def handle_email(task_file: Path):
    """Triage an email note → draft a reply → write to /Pending_Approval."""
    content = task_file.read_text(encoding="utf-8")
    draft = _ask_groq(
        f"You are a professional executive assistant. Read this email note and draft a polite, concise reply.\n\n"
        f"EMAIL NOTE:\n{content}\n\n"
        f"Write ONLY the reply body. No subject line, no extra commentary."
    )
    _write_pending_approval(
        task_name=task_file.stem,
        action="send_email",
        details={"draft_reply": draft, "original_note": str(task_file)},
        summary=f"Draft email reply for: {task_file.name}",
    )
    log.info("Email draft written to Pending_Approval: %s", task_file.name)


def handle_linkedin(task_file: Path):
    """Draft a LinkedIn post → write to /Pending_Approval."""
    content = task_file.read_text(encoding="utf-8")
    draft = _ask_groq(
        f"You are a LinkedIn content strategist. Based on this note, write an engaging LinkedIn post (max 300 words).\n\n"
        f"NOTE:\n{content}\n\nWrite ONLY the post text."
    )
    _write_pending_approval(
        task_name=task_file.stem,
        action="post_linkedin",
        details={"post_text": draft},
        summary="LinkedIn post draft ready for approval",
    )
    log.info("LinkedIn draft written to Pending_Approval: %s", task_file.name)


def handle_social(task_file: Path):
    """Draft social media posts (Facebook) → write to /Pending_Approval."""
    content = task_file.read_text(encoding="utf-8")
    draft = _ask_groq(
        f"You are a social media manager. Based on this note, write a short engaging Facebook post (max 150 words).\n\n"
        f"NOTE:\n{content}\n\nWrite ONLY the post text."
    )
    _write_pending_approval(
        task_name=task_file.stem,
        action="post_social",
        details={"post_text": draft, "platforms": ["facebook"]},
        summary="Social media post draft ready for approval",
    )
    log.info("Social draft written to Pending_Approval: %s", task_file.name)


def handle_plan(task_file: Path):
    """Generate a Plan.md from inbox notes → write to /Plans."""
    content = task_file.read_text(encoding="utf-8")
    plan = _ask_groq(
        f"You are an autonomous executive assistant. Analyse this note and produce a structured Plan.md with:\n"
        f"## 🔴 Urgent\n## 🟡 This Week\n## 🟢 Backlog\n## 💡 Opportunities\n## 📧 Emails to Send\n## 📱 Posts to Draft\n\n"
        f"Each item as a checkbox `- [ ] Action`. Today: {datetime.now().strftime('%Y-%m-%d %A')}\n\n"
        f"NOTE:\n{content}\n\nProduce ONLY valid Markdown."
    )
    plans_dir = VAULT_PATH / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = plans_dir / f"{ts}_Plan_{task_file.stem}.md"
    plan_file.write_text(plan, encoding="utf-8")
    log.info("Plan written: %s", plan_file.name)


def handle_odoo(task_file: Path):
    """Handle Odoo-related tasks (invoice creation, P&L queries) via JSON-RPC."""
    import requests
    content = task_file.read_text(encoding="utf-8")
    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
    odoo_db  = os.getenv("ODOO_DB", "odoo")
    odoo_user = os.getenv("ODOO_USERNAME", "admin")
    odoo_pass = os.getenv("ODOO_PASSWORD", "")

    # Authenticate
    auth_resp = requests.post(f"{odoo_url}/web/dataset/call_kw", json={
        "jsonrpc": "2.0", "method": "call", "id": 1,
        "params": {
            "model": "res.users", "method": "authenticate",
            "args": [odoo_db, odoo_user, odoo_pass, {}], "kwargs": {},
        },
    }, timeout=10)
    uid = auth_resp.json().get("result")
    if not uid:
        raise RuntimeError("Odoo authentication failed")

    log.info("Odoo authenticated as uid=%s. Task: %s", uid, task_file.name)
    # Further Odoo actions would be dispatched here based on task content
    _write_pending_approval(
        task_name=task_file.stem,
        action="odoo_action",
        details={"uid": uid, "note": content[:500]},
        summary=f"Odoo task processed: {task_file.name}",
    )


def handle_default(task_file: Path):
    """Fallback handler — summarise unknown tasks and route to Plans."""
    content = task_file.read_text(encoding="utf-8")
    summary = _ask_groq(
        f"Summarise this task note in 3 bullet points and suggest what to do next:\n\n{content}"
    )
    plans_dir = VAULT_PATH / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (plans_dir / f"{ts}_summary_{task_file.stem}.md").write_text(
        f"# Summary: {task_file.name}\n\n{summary}\n", encoding="utf-8"
    )


# ── HITL Pending Approval Writer ──────────────────────────────────────────────

def _write_pending_approval(task_name: str, action: str, details: dict, summary: str):
    """Write an approval request file to /Pending_Approval."""
    import json
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"APPROVAL_{ts}_{action}_{task_name}.md"
    content = f"""---
type: approval_request
action: {action}
task: {task_name}
created: {datetime.now().isoformat()}
expires: {datetime.now().isoformat()}
status: pending
agent: cloud
---

# ✋ Approval Required: {summary}

**Action:** `{action}`
**Task:** `{task_name}`
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Details
```json
{json.dumps(details, indent=2, default=str)}
```

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.
"""
    (pending_dir / filename).write_text(content, encoding="utf-8")
    log.info("Pending approval written: %s", filename)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Cloud Orchestrator starting (agent=%s) ===", AGENT_NAME)

    # Start vault sync in background thread
    vault_sync = VaultSync(vault_path=str(VAULT_PATH), agent_name=AGENT_NAME)
    sync_thread = threading.Thread(target=vault_sync.run_loop, daemon=True)
    sync_thread.start()
    log.info("Vault sync thread started.")

    # Set up claim orchestrator
    orchestrator = ClaimOrchestrator(
        vault_path=str(VAULT_PATH),
        agent_name=AGENT_NAME,
        poll_interval=int(os.getenv("WATCHER_POLL_INTERVAL", "30")),
    )

    # Register task handlers (cloud specialisation)
    orchestrator.register_handler("email",    handle_email)
    orchestrator.register_handler("linkedin", handle_linkedin)
    orchestrator.register_handler("social",   handle_social)
    orchestrator.register_handler("plan",     handle_plan)
    orchestrator.register_handler("odoo",     handle_odoo)
    orchestrator.register_handler("default",  handle_default)

    log.info("Cloud handlers registered. Starting main loop...")
    orchestrator.run()


if __name__ == "__main__":
    main()
