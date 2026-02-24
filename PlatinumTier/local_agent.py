"""
Local Agent – runs on your laptop.

Responsibilities:
  - WhatsApp sessions (Playwright-based)
  - Payment approvals (HITL: watches /Approved folder)
  - Final send/post (executes approved actions via MCP servers)
  - Dashboard.md updates (single writer = Local)
  - Wakes up automatically when laptop is opened

Does NOT: triage email, draft social posts — those stay Cloud.

Claim specialisation: handles task types: whatsapp, payment, approval_execute
"""
import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from claim_orchestrator import ClaimOrchestrator
from vault_sync import VaultSync

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LocalAgent] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("local_agent.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("LocalAgent")

VAULT_PATH  = Path(os.getenv("VAULT_PATH", "./Vault")).resolve()
GROQ_MODEL  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AGENT_NAME  = "local"

_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _ask_groq(prompt: str, max_tokens: int = 1024) -> str:
    resp = _groq.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


# ── Approval Watcher ──────────────────────────────────────────────────────────

class ApprovalWatcher:
    """
    Watches /Approved and /Rejected folders.
    When a file appears in /Approved → execute the action via MCP.
    When a file appears in /Rejected → log and archive.
    """

    def __init__(self, vault_path: Path, poll_interval: int = 5):
        self.approved  = vault_path / "Approved"
        self.rejected  = vault_path / "Rejected"
        self.done      = vault_path / "Done"
        self.poll_interval = poll_interval
        for d in [self.approved, self.rejected, self.done]:
            d.mkdir(parents=True, exist_ok=True)

    def _execute_approved(self, filepath: Path):
        """Parse approval file and execute the action."""
        content = filepath.read_text(encoding="utf-8")
        # Extract action from frontmatter
        action = "unknown"
        for line in content.splitlines():
            if line.startswith("action:"):
                action = line.split(":", 1)[1].strip()
                break

        log.info("Executing approved action: %s (%s)", action, filepath.name)

        try:
            if action == "send_email":
                self._execute_send_email(content)
            elif action == "post_linkedin":
                self._execute_post_linkedin(content)
            elif action == "post_social":
                self._execute_post_social(content)
            elif action == "payment":
                self._execute_payment(content)
            elif action == "whatsapp_reply":
                self._execute_whatsapp_reply(content)
            else:
                log.warning("Unknown action type: %s", action)

            # Move to Done
            dest = self.done / filepath.name
            filepath.rename(dest)
            log.info("Action executed and archived: %s → Done/", filepath.name)

        except Exception as exc:
            log.error("Failed to execute %s: %s", action, exc)

    def _execute_send_email(self, content: str):
        """Send email via SMTP."""
        import smtplib
        from email.mime.text import MIMEText
        # Extract draft from JSON block in content
        draft = self._extract_json_field(content, "draft_reply")
        to_addr = self._extract_json_field(content, "to") or os.getenv("HEALTH_ALERT_EMAIL", "")
        if not draft or not to_addr:
            log.warning("send_email: missing draft or recipient.")
            return
        msg = MIMEText(draft)
        msg["Subject"] = "Re: (AI Employee Draft)"
        msg["From"]    = os.getenv("GMAIL_EMAIL", "")
        msg["To"]      = to_addr
        with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(os.getenv("GMAIL_EMAIL", ""), os.getenv("GMAIL_APP_PASSWORD", ""))
            s.send_message(msg)
        log.info("Email sent to %s", to_addr)

    def _execute_post_linkedin(self, content: str):
        """Post to LinkedIn via API."""
        import requests
        post_text = self._extract_json_field(content, "post_text")
        if not post_text:
            log.warning("post_linkedin: missing post_text.")
            return
        token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        urn   = os.getenv("LINKEDIN_PERSON_URN", "")
        resp  = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "author": urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            },
            timeout=15,
        )
        resp.raise_for_status()
        log.info("LinkedIn post published. Status: %s", resp.status_code)

    def _execute_post_social(self, content: str):
        """Post to Facebook page."""
        import requests
        post_text = self._extract_json_field(content, "post_text")
        page_id   = os.getenv("FACEBOOK_PAGE_ID", "")
        token     = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        if not post_text or not page_id or not token:
            log.warning("post_social: missing credentials or text.")
            return
        resp = requests.post(
            f"https://graph.facebook.com/{page_id}/feed",
            data={"message": post_text, "access_token": token},
            timeout=15,
        )
        resp.raise_for_status()
        log.info("Facebook post published. Response: %s", resp.json())

    def _execute_payment(self, content: str):
        """Log payment approval — actual transfer requires browser MCP."""
        amount    = self._extract_json_field(content, "amount")
        recipient = self._extract_json_field(content, "recipient")
        log.info("PAYMENT APPROVED: $%s to %s — trigger browser MCP to complete.", amount, recipient)
        # In production: call browser MCP to log into payment portal

    def _execute_whatsapp_reply(self, content: str):
        """Send WhatsApp reply via Business API."""
        import requests
        reply_text = self._extract_json_field(content, "reply_text")
        phone_number = self._extract_json_field(content, "to_phone")
        token = os.getenv("WHATSAPP_API_TOKEN", "")
        phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        if not reply_text or not phone_number:
            log.warning("whatsapp_reply: missing reply_text or phone number.")
            return
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": reply_text},
            },
            timeout=15,
        )
        resp.raise_for_status()
        log.info("WhatsApp reply sent to %s", phone_number)

    def _extract_json_field(self, content: str, field: str) -> str | None:
        """Extract a field from the JSON block in an approval file."""
        try:
            match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                return data.get(field)
        except Exception:
            pass
        return None

    def run(self):
        """Poll /Approved and /Rejected for files to act on."""
        log.info("ApprovalWatcher started.")
        while True:
            for filepath in sorted(self.approved.glob("*.md")):
                try:
                    self._execute_approved(filepath)
                except Exception as exc:
                    log.error("ApprovalWatcher error on %s: %s", filepath.name, exc)
            for filepath in sorted(self.rejected.glob("*.md")):
                dest = self.done / f"REJECTED_{filepath.name}"
                filepath.rename(dest)
                log.info("Rejected action archived: %s", filepath.name)
            time.sleep(self.poll_interval)


# ── Dashboard Updater ─────────────────────────────────────────────────────────

def update_dashboard():
    """Update Dashboard.md with current counts (Local is single writer)."""
    dashboard = VAULT_PATH / "Dashboard.md"
    needs_action   = len(list((VAULT_PATH / "Needs_Action").glob("*.md")))
    pending        = len(list((VAULT_PATH / "Pending_Approval").glob("*.md")))
    inbox          = len(list((VAULT_PATH / "Inbox").glob("*.md")))
    now            = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""# 🏆 AI Employee Dashboard
> Last updated: {now} (Local Agent)

## 📊 Live Status
| Metric | Count |
|--------|-------|
| 📥 Inbox | {inbox} |
| ⚡ Needs Action | {needs_action} |
| ✋ Pending Approval | {pending} |

## 🤖 Agent Status
| Agent | Mode | Status |
|-------|------|--------|
| Cloud Orchestrator | Always-On VM | 🟢 Running |
| Local Agent | Laptop | 🟢 Active |
| Vault Sync | Git | 🔄 Auto |

## 📁 Quick Links
- [[Inbox/]]
- [[Needs_Action/]]
- [[Pending_Approval/]]
- [[Plans/]]
- [[Done/]]
- [[Company_Handbook]]
"""
    dashboard.write_text(content, encoding="utf-8")


def dashboard_loop(interval: int = 60):
    while True:
        try:
            update_dashboard()
        except Exception as exc:
            log.error("Dashboard update error: %s", exc)
        time.sleep(interval)


# ── Task Handlers (Local specialisation) ─────────────────────────────────────

def handle_whatsapp(task_file: Path):
    """Process a WhatsApp task — draft reply and write to /Pending_Approval."""
    content = task_file.read_text(encoding="utf-8")
    reply = _ask_groq(
        f"You are a polite business assistant. Draft a WhatsApp reply to this message.\n\n"
        f"MESSAGE:\n{content}\n\nWrite ONLY the reply text. Keep it under 100 words."
    )
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"APPROVAL_{ts}_whatsapp_reply_{task_file.stem}.md"
    (pending_dir / filename).write_text(
        f"""---\ntype: approval_request\naction: whatsapp_reply\ntask: {task_file.stem}\ncreated: {datetime.now().isoformat()}\nstatus: pending\nagent: local\n---\n\n"""
        f"# ✋ WhatsApp Reply Approval\n\n**Draft:**\n\n> {reply}\n\n"
        f"## Details\n```json\n{{\"reply_text\": {json.dumps(reply)}, \"to_phone\": \"FILL_IN\"}}\n```\n\n"
        f"Move to `/Approved` to send, `/Rejected` to discard.\n",
        encoding="utf-8",
    )
    log.info("WhatsApp reply draft written to Pending_Approval.")


def handle_payment(task_file: Path):
    """Flag payment for human approval."""
    content = task_file.read_text(encoding="utf-8")
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"APPROVAL_{ts}_payment_{task_file.stem}.md"
    (pending_dir / filename).write_text(
        f"""---\ntype: approval_request\naction: payment\ntask: {task_file.stem}\ncreated: {datetime.now().isoformat()}\nstatus: pending\nagent: local\n---\n\n"""
        f"# ✋ Payment Approval Required\n\n{content}\n\n"
        f"## Details\n```json\n{{\"amount\": \"SEE_ABOVE\", \"recipient\": \"SEE_ABOVE\"}}\n```\n\n"
        f"Move to `/Approved` to execute payment, `/Rejected` to cancel.\n",
        encoding="utf-8",
    )
    log.info("Payment approval written: %s", filename)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Local Agent starting (agent=%s) ===", AGENT_NAME)

    # Ensure all vault folders exist
    for folder in ["Inbox", "Needs_Action", "In_Progress/local", "In_Progress/cloud",
                   "Plans", "Pending_Approval", "Approved", "Rejected", "Updates", "Done"]:
        (VAULT_PATH / folder).mkdir(parents=True, exist_ok=True)

    # Start vault sync in background
    vault_sync = VaultSync(vault_path=str(VAULT_PATH), agent_name=AGENT_NAME)
    sync_thread = threading.Thread(target=vault_sync.run_loop, daemon=True)
    sync_thread.start()
    log.info("Vault sync thread started.")

    # Start approval watcher in background
    approval_watcher = ApprovalWatcher(vault_path=VAULT_PATH)
    approval_thread = threading.Thread(target=approval_watcher.run, daemon=True)
    approval_thread.start()
    log.info("Approval watcher thread started.")

    # Start dashboard updater in background
    dash_thread = threading.Thread(target=dashboard_loop, daemon=True)
    dash_thread.start()
    log.info("Dashboard updater thread started.")

    # Set up claim orchestrator (local specialisation)
    orchestrator = ClaimOrchestrator(
        vault_path=str(VAULT_PATH),
        agent_name=AGENT_NAME,
        poll_interval=int(os.getenv("WATCHER_POLL_INTERVAL", "15")),
    )
    orchestrator.register_handler("whatsapp", handle_whatsapp)
    orchestrator.register_handler("payment",  handle_payment)

    log.info("Local handlers registered. Starting main loop...")
    orchestrator.run()


if __name__ == "__main__":
    main()
