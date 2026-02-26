from flask import Flask, request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json, os, threading, sys

load_dotenv("BronzeTier/.env")

# Add BronzeTier to path so we can import the Orchestrator
_BRONZE_DIR = Path(__file__).resolve().parent / "BronzeTier"
if str(_BRONZE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRONZE_DIR))

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "myhackathonverifytoken")

# Single vault — always BronzeTier/Vault
VAULT_PATH = Path(os.getenv("VAULT_PATH", "BronzeTier/Vault"))
VAULT_NEEDS_ACTION = VAULT_PATH / "Needs_Action"
VAULT_NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

# Lazy orchestrator instance (shared across requests)
_orchestrator = None
_orchestrator_lock = threading.Lock()

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        with _orchestrator_lock:
            if _orchestrator is None:
                try:
                    from Orchestrator import Orchestrator
                    _orchestrator = Orchestrator()
                    print("[Webhook] Orchestrator loaded ✅")
                except Exception as e:
                    print(f"[Webhook] Could not load Orchestrator: {e}")
    return _orchestrator


def _trigger_orchestrator(filepath: Path):
    """Run orchestrator reasoning on a file in a background thread."""
    try:
        orch = get_orchestrator()
        if orch:
            orch.process_needs_action_file(filepath)
            print(f"[Webhook] Orchestrator processed: {filepath.name}")
        else:
            print(f"[Webhook] Orchestrator unavailable — creating approval file directly")
            _create_approval_fallback(filepath)
    except Exception as e:
        print(f"[Webhook] Orchestrator error: {e} — creating approval file directly")
        _create_approval_fallback(filepath)


def _create_approval_fallback(filepath: Path):
    """Create a Pending_Approval file directly if orchestrator is unavailable."""
    try:
        content = filepath.read_text(encoding="utf-8")
        # Extract from/message from the file
        from_line = next((l for l in content.splitlines() if l.startswith("from:")), "from: unknown")
        from_number = from_line.replace("from:", "").strip()
        msg_line = next((l for l in content.splitlines() if l.startswith("# 📱")), "")
        subject = msg_line.replace("# 📱 WhatsApp:", "").strip()

        # Read body
        body_start = content.find("## Message\n")
        body = content[body_start + 12:].split("##")[0].strip() if body_start > 0 else subject

        pending_dir = VAULT_PATH / "Pending_Approval"
        pending_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        approval_file = pending_dir / f"APPROVAL_REQUIRED_WHATSAPP_{filepath.stem}_{ts}.md"

        approval_content = f"""---
type: approval_request
action: whatsapp_reply
priority: high
status: pending_approval
from: {from_number}
created: {datetime.now().isoformat()}
source_file: {filepath.name}
---

# ⚠️ Approval Required: WhatsApp Reply

**From:** {from_number}
**Message:** {body}
**Priority:** HIGH 🔴

## AI Suggested Reply

```json
{{
  "to_phone": "{from_number}",
  "reply_text": "Hi! I received your urgent message: '{body[:80]}'. I am reviewing it now and will respond shortly."
}}
```

## How to Respond
- **Approve**: Move this file to `Approved/` → AI auto-sends WhatsApp reply within 5 seconds
- **Reject**: Move this file to `Rejected/` → No action taken
- **Custom reply**: Edit `reply_text` above before moving to `Approved/`
"""
        approval_file.write_text(approval_content, encoding="utf-8")
        print(f"[Webhook] Approval file created: {approval_file.name}")
    except Exception as e:
        print(f"[Webhook] Fallback approval creation failed: {e}")


def send_whatsapp_reply(to_phone: str, message: str) -> dict:
    """Send a WhatsApp reply via the Business Cloud API."""
    token    = os.getenv("WHATSAPP_API_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    import requests as req
    r = req.post(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message},
        },
        timeout=15,
    )
    return {"status": r.status_code, "response": r.json()}


def save_whatsapp_message(data: dict):
    """Parse incoming WhatsApp Cloud API payload and save to vault."""
    try:
        entries = data.get("entry", [])
        if not entries:
            print("[WhatsApp] No entries in payload")
            return

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Skip status updates (delivery receipts) — not real messages
                if value.get("statuses"):
                    print(f"[WhatsApp] Status update received (delivery receipt) — skipping")
                    continue

                messages = value.get("messages", [])
                if not messages:
                    print(f"[WhatsApp] No messages in payload: {list(value.keys())}")
                    continue

                _process_messages(messages)

    except Exception as e:
        print(f"[WhatsApp] Error parsing payload: {e}")
        print(f"[WhatsApp] Raw data: {json.dumps(data)[:500]}")


def _process_messages(messages: list):
    """Process a list of WhatsApp message objects."""
    try:

        for msg in messages:
            msg_id = msg.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
            from_number = msg.get("from", "unknown")
            timestamp = msg.get("timestamp", "")
            msg_type = msg.get("type", "text")

            if msg_type == "text":
                body = msg.get("text", {}).get("body", "")
            elif msg_type == "audio":
                body = "[Audio message received]"
            elif msg_type == "image":
                body = "[Image received]"
            else:
                body = f"[{msg_type} message received]"

            # Detect urgency keywords
            urgency = "high" if any(w in body.lower() for w in ["urgent", "asap", "emergency", "money", "send", "help"]) else "normal"

            content = f"""---
type: whatsapp
from: {from_number}
received: {datetime.now().isoformat()}
priority: {urgency}
status: pending
message_id: {msg_id}
---

# 📱 WhatsApp: {body[:60]}

**From:** {from_number}
**Received:** {datetime.fromtimestamp(int(timestamp)).isoformat() if timestamp else datetime.now().isoformat()}
**Priority:** {urgency.upper()}

## Message
{body}

## Suggested Actions
- [ ] Reply to sender
- [ ] Escalate if urgent
- [ ] Archive after processing
"""
            filepath = VAULT_NEEDS_ACTION / f"WHATSAPP_{msg_id}.md"
            filepath.write_text(content, encoding="utf-8")
            print(f"[WhatsApp] Saved message from {from_number}: {body[:80]}")

            # AUTO-TRIGGER orchestrator reasoning for HIGH priority messages
            if urgency == "high":
                print(f"[WhatsApp] 🔴 HIGH priority — triggering orchestrator reasoning...")
                threading.Thread(
                    target=_trigger_orchestrator,
                    args=(filepath,),
                    daemon=True,
                    name=f"orch-{msg_id[:8]}"
                ).start()

    except Exception as e:
        print(f"[WhatsApp] Error parsing message: {e}")
        print(f"[WhatsApp] Messages: {json.dumps(messages)[:300]}")


@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print(f"[WhatsApp] Webhook verified ✅")
            return challenge, 200
        else:
            return "Forbidden", 403
    else:
        data = request.json or {}
        print(f"[WhatsApp] Incoming: {json.dumps(data)[:200]}")
        save_whatsapp_message(data)
        return "Event received", 200


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "vault": str(VAULT_NEEDS_ACTION)}, 200


@app.route("/reply/whatsapp", methods=["POST"])
def reply_whatsapp():
    """
    Send a WhatsApp reply manually or from HITL approval.
    POST JSON: {"to": "923713584557", "message": "Your reply here"}
    """
    data    = request.json or {}
    to      = data.get("to", "")
    message = data.get("message", "")
    if not to or not message:
        return {"error": "Missing 'to' or 'message'"}, 400
    result = send_whatsapp_reply(to, message)
    print(f"[WhatsApp] Reply sent to {to}: {message[:60]}")
    return result, result.get("status", 200)


@app.route("/reply/whatsapp/<phone>", methods=["GET"])
def reply_whatsapp_quick(phone):
    """
    Quick reply via browser URL.
    GET /reply/whatsapp/923713584557?msg=Your+reply+here
    """
    message = request.args.get("msg", "")
    if not message:
        return {"error": "Missing ?msg= query param"}, 400
    result = send_whatsapp_reply(phone, message)
    print(f"[WhatsApp] Quick reply sent to {phone}: {message[:60]}")
    return result, result.get("status", 200)


if __name__ == "__main__":
    app.run(port=3000, debug=False)
