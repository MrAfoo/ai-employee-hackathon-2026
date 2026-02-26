"""
gmail_imap_watcher.py – Persistent Gmail watcher using IMAP.

Polls Gmail every 60s for unread important emails, writes .md notes
to BronzeTier/Vault/Needs_Action/, and auto-triggers orchestrator
for HIGH priority emails (urgent/payment/invoice keywords).

No OAuth2 needed — uses Gmail App Password (GMAIL_APP_PASSWORD in .env).

Usage:
    python BronzeTier/watchers/gmail_imap_watcher.py
"""
import email
import imaplib
import logging
import os
import sys
import time
import threading
from datetime import datetime
from email.header import decode_header
from pathlib import Path

from dotenv import load_dotenv

load_dotenv('BronzeTier/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [GmailWatcher] %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gmail_watcher.log', encoding='utf-8'),
    ],
)
log = logging.getLogger('GmailWatcher')

VAULT_PATH       = Path(os.getenv('VAULT_PATH', 'BronzeTier/Vault'))
NEEDS_ACTION     = VAULT_PATH / 'Needs_Action'
NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

GMAIL_EMAIL      = os.getenv('GMAIL_EMAIL', '')
GMAIL_PASSWORD   = os.getenv('GMAIL_APP_PASSWORD', '')
POLL_INTERVAL    = int(os.getenv('GMAIL_POLL_INTERVAL', '60'))

# Keywords that flag an email as HIGH priority
URGENT_KEYWORDS  = ['urgent', 'asap', 'emergency', 'payment', 'invoice',
                    'overdue', 'immediately', 'critical', 'wire transfer', 'refund']

_processed_ids: set[str] = set()


def _decode_str(value: str) -> str:
    """Decode encoded email header value."""
    parts = decode_header(value or '')
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            decoded.append(part)
    return ' '.join(decoded)


def _connect() -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
    return mail


def _get_body(msg) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                try:
                    return part.get_payload(decode=True).decode('utf-8', errors='replace')
                except Exception:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except Exception:
            pass
    return ''


def _save_email(uid: str, msg) -> Path:
    """Parse email and write .md note to Needs_Action."""
    subject  = _decode_str(msg.get('Subject', '(no subject)'))
    sender   = _decode_str(msg.get('From', 'Unknown'))
    date_str = msg.get('Date', datetime.now().isoformat())
    body     = _get_body(msg)[:2000]  # cap at 2000 chars

    # Detect urgency
    combined = (subject + ' ' + body).lower()
    urgency  = 'high' if any(kw in combined for kw in URGENT_KEYWORDS) else 'normal'

    content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: {urgency}
status: pending
message_id: {uid}
---

# 📧 Email: {subject}

**From:** {sender}
**Subject:** {subject}
**Received:** {date_str}
**Priority:** {urgency.upper()}

## Email Content
{body}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
    safe_uid = uid.replace(' ', '_')
    filepath = NEEDS_ACTION / f'EMAIL_{safe_uid}.md'
    filepath.write_text(content, encoding='utf-8')
    log.info('Saved email [%s priority]: %s → %s', urgency.upper(), subject[:60], filepath.name)

    # Auto-trigger orchestrator for HIGH priority
    if urgency == 'high':
        log.info('🔴 HIGH priority email — triggering orchestrator...')
        threading.Thread(target=_trigger_orchestrator, args=(filepath,), daemon=True).start()

    return filepath


def _trigger_orchestrator(filepath: Path):
    """Trigger the main orchestrator to reason about this email."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Orchestrator import Orchestrator
        orch = Orchestrator()
        orch.process_needs_action_file(filepath)
        log.info('Orchestrator processed: %s', filepath.name)
    except Exception as e:
        log.warning('Orchestrator trigger failed (will be picked up on next cycle): %s', e)


def poll_once():
    """Connect to Gmail, fetch unseen emails, save new ones."""
    try:
        mail = _connect()
        mail.select('inbox')

        # Fetch all unseen emails
        status, data = mail.search(None, 'UNSEEN')
        if status != 'OK':
            log.warning('IMAP search failed: %s', status)
            mail.logout()
            return

        uids = data[0].split()
        new  = [u.decode() for u in uids if u.decode() not in _processed_ids]
        # Only process the 10 most recent emails per cycle to avoid flooding vault
        new  = new[-10:]
        log.info('Found %d new unread emails (processing last 10).', len(new))

        for uid in new[:10]:  # max 10 per cycle
            try:
                status, msg_data = mail.fetch(uid, '(RFC822)')
                if status != 'OK':
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                _save_email(uid, msg)
                _processed_ids.add(uid)
            except Exception as e:
                log.error('Error processing email UID %s: %s', uid, e)

        mail.logout()

    except imaplib.IMAP4.error as e:
        log.error('IMAP error: %s — will retry next cycle', e)
    except Exception as e:
        log.error('Unexpected error: %s', e)


def run():
    """Main loop — poll Gmail every POLL_INTERVAL seconds."""
    if not GMAIL_EMAIL or not GMAIL_PASSWORD:
        log.error('GMAIL_EMAIL and GMAIL_APP_PASSWORD must be set in BronzeTier/.env')
        sys.exit(1)

    log.info('Gmail IMAP Watcher started.')
    log.info('  Account      : %s', GMAIL_EMAIL)
    log.info('  Vault        : %s', VAULT_PATH.resolve())
    log.info('  Poll interval: %ds', POLL_INTERVAL)
    log.info('  Urgent words : %s', ', '.join(URGENT_KEYWORDS))

    while True:
        poll_once()
        log.info('Next check in %ds...', POLL_INTERVAL)
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    run()
