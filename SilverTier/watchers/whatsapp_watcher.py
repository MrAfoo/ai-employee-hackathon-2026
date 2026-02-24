"""
WhatsApp Watcher – monitors WhatsApp exports or Business API webhooks
and writes notes into the Obsidian vault Inbox.

Two modes:
  A) Local export folder (free, no API needed):
     - Open WhatsApp → chat → ⋮ → Export chat → save .txt to WHATSAPP_EXPORT_FOLDER
     - This watcher detects new .txt files and parses them.
  B) WhatsApp Business API (webhook mode):
     - Runs a small HTTP server to receive real-time message webhooks.
"""
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WhatsAppWatcher] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mode A: Local export folder watcher
# ---------------------------------------------------------------------------

class WhatsAppExportWatcher:
    """
    Watches a folder for WhatsApp chat export .txt files and writes
    a Markdown note to the vault Inbox for each new export found.
    """

    TIMESTAMP_RE = re.compile(
        r"^\[?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]?\s*(.+?):\s(.+)$"
    )

    def __init__(
        self,
        vault_path: str,
        export_folder: str | None = None,
        poll_interval: int | None = None,
    ):
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.export_folder = Path(
            export_folder or os.getenv("WHATSAPP_EXPORT_FOLDER", "./whatsapp_exports")
        ).resolve()
        self.poll_interval = poll_interval or int(os.getenv("WATCHER_POLL_INTERVAL", "60"))
        self._processed: set[str] = set()

    def _parse_export(self, filepath: Path) -> list[dict]:
        """Parse a WhatsApp .txt export into a list of message dicts."""
        messages = []
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                m = self.TIMESTAMP_RE.match(line.strip())
                if m:
                    messages.append({
                        "date": m.group(1),
                        "time": m.group(2),
                        "sender": m.group(3).strip(),
                        "message": m.group(4).strip(),
                    })
        except Exception as exc:
            log.error("Failed to parse %s: %s", filepath, exc)
        return messages

    def _write_note(self, filepath: Path, messages: list[dict]):
        """Write a vault Inbox note for a WhatsApp export file."""
        inbox = self.vault_path / "Inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = filepath.stem.replace(" ", "_")[:50]
        note_file = inbox / f"{timestamp}_whatsapp_{safe_name}.md"

        lines = [f"- **{m['sender']}** [{m['date']} {m['time']}]: {m['message']}" for m in messages]
        body = "\n".join(lines) if lines else "_No messages parsed._"

        content = f"""---
title: "WhatsApp Export: {filepath.name}"
created: {datetime.now().isoformat()}
source: whatsapp
tags: [inbox, whatsapp]
---

# WhatsApp Export: {filepath.name}

**File:** `{filepath}`  
**Messages:** {len(messages)}  
**Imported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{body}
"""
        note_file.write_text(content, encoding="utf-8")
        log.info("Note written: %s (%d messages)", note_file.name, len(messages))

    def run(self):
        """Poll the export folder for new .txt files."""
        log.info("WhatsApp export watcher started on: %s", self.export_folder)
        self.export_folder.mkdir(parents=True, exist_ok=True)
        while True:
            for f in self.export_folder.glob("*.txt"):
                if str(f) not in self._processed:
                    messages = self._parse_export(f)
                    if messages:
                        self._write_note(f, messages)
                    self._processed.add(str(f))
            time.sleep(self.poll_interval)


# ---------------------------------------------------------------------------
# Mode B: WhatsApp Business API webhook server
# ---------------------------------------------------------------------------

def create_webhook_app(vault_path: str):
    """
    Create a FastAPI webhook receiver for WhatsApp Business API messages.
    Mount at POST /webhook and GET /webhook (for verification).
    """
    try:
        from fastapi import FastAPI, Request, Query
        from fastapi.responses import PlainTextResponse
    except ImportError:
        raise ImportError("Install fastapi and uvicorn: pip install fastapi uvicorn")

    vault = Path(vault_path).expanduser().resolve()
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_verify_token")
    app = FastAPI(title="WhatsApp Webhook")

    @app.get("/webhook")
    async def verify(
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_token: str = Query(None, alias="hub.verify_token"),
        hub_challenge: str = Query(None, alias="hub.challenge"),
    ):
        if hub_mode == "subscribe" and hub_token == verify_token:
            log.info("WhatsApp webhook verified.")
            return PlainTextResponse(hub_challenge)
        return PlainTextResponse("Forbidden", status_code=403)

    @app.post("/webhook")
    async def receive(request: Request):
        data = await request.json()
        try:
            entry = data["entry"][0]["changes"][0]["value"]
            messages = entry.get("messages", [])
            for msg in messages:
                sender = msg.get("from", "unknown")
                msg_type = msg.get("type", "text")
                body = msg.get("text", {}).get("body", f"[{msg_type} message]")
                _write_webhook_note(vault, sender, body)
        except (KeyError, IndexError) as e:
            log.warning("Unexpected webhook payload: %s", e)
        return {"status": "ok"}

    return app


def _write_webhook_note(vault: Path, sender: str, body: str):
    inbox = vault / "Inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    note_file = inbox / f"{timestamp}_whatsapp_msg_{sender}.md"
    content = f"""---
title: "WhatsApp Message from {sender}"
created: {datetime.now().isoformat()}
source: whatsapp_api
tags: [inbox, whatsapp]
---

# WhatsApp Message

**From:** {sender}  
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{body}
"""
    note_file.write_text(content, encoding="utf-8")
    log.info("Webhook note written: %s", note_file.name)


if __name__ == "__main__":
    import sys
    vault = os.getenv("VAULT_PATH", "./BronzeTier")
    mode = sys.argv[1] if len(sys.argv) > 1 else "export"
    if mode == "webhook":
        import uvicorn
        app = create_webhook_app(vault_path=vault)
        uvicorn.run(app, host="0.0.0.0", port=8003)
    else:
        watcher = WhatsAppExportWatcher(vault_path=vault)
        watcher.run()
