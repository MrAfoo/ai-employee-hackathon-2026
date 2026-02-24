"""
email_mcp_server.py – Silver Tier MCP Email Server

A FastAPI server that acts as the "email hands" for the AI Employee.
The Bronze Tier Orchestrator calls this server when an email action is approved.

Endpoints:
  POST /send        – Send an email via Gmail SMTP
  POST /draft       – Save a draft (to Vault/Drafts/)
  GET  /health      – Health check
  GET  /sent        – List recently sent emails

Usage:
  python email_mcp_server.py
  # Server starts on http://localhost:8001

Configure in BronzeTier/.env:
  EMAIL_MCP_URL=http://localhost:8001
"""

import json
import logging
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr

# Load env from BronzeTier first, then SilverTier
for env_path in ["../BronzeTier/.env", ".env", "../.env"]:
    if Path(env_path).exists():
        load_dotenv(env_path)
        break

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EmailMCP] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("email_mcp.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("EmailMCP")

# ── Config ────────────────────────────────────────────────────────────────────
GMAIL_EMAIL        = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SMTP_HOST          = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT          = int(os.getenv("SMTP_PORT", "587"))
VAULT_PATH         = Path(os.getenv("VAULT_PATH", "../Vault")).resolve()
DRAFTS_PATH        = VAULT_PATH / "Drafts"
SENT_LOG           = VAULT_PATH / "Accounting" / "sent_emails.jsonl"
MCP_PORT           = int(os.getenv("EMAIL_MCP_PORT", "8001"))

DRAFTS_PATH.mkdir(parents=True, exist_ok=True)
SENT_LOG.parent.mkdir(parents=True, exist_ok=True)

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Employee – Email MCP Server",
    description="Silver Tier MCP server for sending emails on behalf of the AI Employee.",
    version="1.0.0",
)

# Track recently sent emails in memory
_sent_log: list[dict] = []


# ── Models ────────────────────────────────────────────────────────────────────
class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: Optional[str] = None
    draft_reply: Optional[str] = None
    description: Optional[str] = None
    action: Optional[str] = "send_email"
    source_file: Optional[str] = None


class DraftEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    source_file: Optional[str] = None


class EmailResponse(BaseModel):
    success: bool
    message: str
    timestamp: str


# ── Email Sender ──────────────────────────────────────────────────────────────
def _send_gmail(to: str, subject: str, body: str) -> str:
    """Send email via Gmail SMTP with App Password."""
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        raise ValueError(
            "GMAIL_EMAIL or GMAIL_APP_PASSWORD not set in .env. "
            "Get an App Password at: https://myaccount.google.com/apppasswords"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_EMAIL
    msg["To"]      = to
    msg["X-Mailer"] = "AI Employee MCP Server"

    # Plain text part
    msg.attach(MIMEText(body, "plain"))

    log.info("Sending email to %s — Subject: %s", to, subject)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    result = f"Email sent to {to} at {datetime.now().isoformat()}"
    log.info("✅ %s", result)
    return result


def _log_sent(to: str, subject: str, body: str, source_file: str = ""):
    """Log sent email to JSONL audit file and memory."""
    record = {
        "timestamp": datetime.now().isoformat(),
        "to": to,
        "subject": subject,
        "preview": body[:200],
        "source_file": source_file,
    }
    with SENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    _sent_log.append(record)
    if len(_sent_log) > 100:
        _sent_log.pop(0)


def _save_draft(to: str, subject: str, body: str, source_file: str = "") -> Path:
    """Save email as a draft .md file in Vault/Drafts/."""
    now = datetime.now()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject)[:40]
    draft_path = DRAFTS_PATH / f"DRAFT_{now.strftime('%Y%m%d_%H%M%S')}_{safe}.md"
    content = f"""---
type: email_draft
to: {to}
subject: {subject}
created: {now.isoformat()}
source_file: {source_file}
status: draft
---

## To
{to}

## Subject
{subject}

## Body
{body}

---
*Draft saved by AI Employee MCP Email Server*
"""
    draft_path.write_text(content, encoding="utf-8")
    log.info("Draft saved: %s", draft_path.name)
    return draft_path


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Health check endpoint."""
    configured = bool(GMAIL_EMAIL and GMAIL_APP_PASSWORD)
    return {
        "status": "ok",
        "gmail_configured": configured,
        "gmail_account": GMAIL_EMAIL if configured else "not configured",
        "vault_path": str(VAULT_PATH),
        "sent_count": len(_sent_log),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/send", response_model=EmailResponse)
async def send_email(req: SendEmailRequest):
    """Send an email. Called by Bronze Tier Orchestrator on HITL approval."""
    body = req.body or req.draft_reply or ""

    if not req.to:
        raise HTTPException(status_code=400, detail="Missing 'to' field")
    if not body:
        raise HTTPException(status_code=400, detail="Missing 'body' or 'draft_reply' field")

    try:
        result = _send_gmail(req.to, req.subject, body)
        _log_sent(req.to, req.subject, body, req.source_file or "")
        return EmailResponse(
            success=True,
            message=result,
            timestamp=datetime.now().isoformat(),
        )
    except ValueError as e:
        # Config error — not a transient failure
        raise HTTPException(status_code=503, detail=str(e))
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Gmail authentication failed. Check GMAIL_APP_PASSWORD in .env"
        )
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {e}")
    except Exception as e:
        log.error("Unexpected error sending email: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/draft", response_model=EmailResponse)
async def save_draft(req: DraftEmailRequest):
    """Save email as a draft in Vault/Drafts/ without sending."""
    try:
        draft_path = _save_draft(req.to, req.subject, req.body, req.source_file or "")
        return EmailResponse(
            success=True,
            message=f"Draft saved: {draft_path.name}",
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sent")
def list_sent(limit: int = 20):
    """List recently sent emails."""
    return {
        "sent": _sent_log[-limit:],
        "total": len(_sent_log),
    }


@app.post("/test")
async def test_send(request: Request):
    """Send a test email to yourself to verify configuration."""
    body = await request.json()
    test_to = body.get("to", GMAIL_EMAIL)
    try:
        result = _send_gmail(
            test_to,
            "✅ AI Employee MCP Email Server – Test",
            f"This is a test email from your AI Employee.\n\nServer is working correctly.\n\nTimestamp: {datetime.now().isoformat()}"
        )
        _log_sent(test_to, "Test Email", "Test email body", "manual_test")
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    log.info("=" * 50)
    log.info("AI Employee – MCP Email Server started")
    log.info("Gmail account : %s", GMAIL_EMAIL or "NOT CONFIGURED")
    log.info("Vault path    : %s", VAULT_PATH)
    log.info("Drafts path   : %s", DRAFTS_PATH)
    log.info("Listening on  : http://localhost:%d", MCP_PORT)
    log.info("=" * 50)
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        log.warning("⚠️  GMAIL_EMAIL or GMAIL_APP_PASSWORD not set — /send will fail")
        log.warning("   Get App Password at: https://myaccount.google.com/apppasswords")


if __name__ == "__main__":
    uvicorn.run(
        "email_mcp_server:app",
        host="0.0.0.0",
        port=MCP_PORT,
        reload=False,
        log_level="info",
    )
