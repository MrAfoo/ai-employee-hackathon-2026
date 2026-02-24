"""
hitl_orchestrator.py – Human-in-the-Loop Approval Orchestrator.

Watches /Pending_Approval, /Approved, and /Rejected folders.
When you move a file from /Pending_Approval to /Approved:
  → The orchestrator reads the action details and calls the appropriate MCP server.
When you move a file to /Rejected:
  → The orchestrator logs and archives it.

This is the "hands" that only act after you give permission.

Usage:
  python hitl_orchestrator.py

The orchestrator runs continuously in the background alongside your watchers.
"""
import json
import logging
import os
import re
import shutil
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HITLOrchestrator] %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('hitl_orchestrator.log', encoding='utf-8'),
    ],
)
log = logging.getLogger('HITLOrchestrator')

VAULT_PATH       = Path(os.getenv('VAULT_PATH', './BronzeTier')).resolve()
PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval'
APPROVED         = VAULT_PATH / 'Approved'
REJECTED         = VAULT_PATH / 'Rejected'
DONE             = VAULT_PATH / 'Done'
AUDIT_LOG        = Path(os.getenv('AUDIT_LOG_PATH', './logs/hitl_audit.jsonl'))
POLL_INTERVAL    = 5  # seconds


def _ensure_folders():
    for folder in [PENDING_APPROVAL, APPROVED, REJECTED, DONE]:
        folder.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def _audit(action: str, filepath: str, result: str, success: bool):
    record = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'file': filepath,
        'result': result,
        'success': success,
    }
    with AUDIT_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, default=str) + '\n')


def _extract_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    meta = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != '---':
        return meta
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' in line:
            key, _, value = line.partition(':')
            meta[key.strip()] = value.strip()
    return meta


def _extract_json_block(content: str) -> dict:
    """Extract JSON from a ```json ... ``` block in the file."""
    match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


# ── Action Executors ──────────────────────────────────────────────────────────

def execute_send_email(details: dict, meta: dict) -> str:
    """Send an email via Gmail SMTP."""
    to_addr  = details.get('to') or os.getenv('HEALTH_ALERT_EMAIL', '')
    subject  = details.get('subject', 'Re: (AI Employee)')
    body     = details.get('draft_reply') or details.get('body', '')

    if not to_addr or not body:
        return 'Missing recipient or body — email not sent.'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = os.getenv('GMAIL_EMAIL', '')
    msg['To']      = to_addr

    with smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', '587'))) as s:
        s.starttls()
        s.login(os.getenv('GMAIL_EMAIL', ''), os.getenv('GMAIL_APP_PASSWORD', ''))
        s.send_message(msg)
    return f'Email sent to {to_addr}'


def execute_post_linkedin(details: dict, meta: dict) -> str:
    """Post to LinkedIn via API."""
    post_text = details.get('post_text', '')
    token     = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    urn       = os.getenv('LINKEDIN_PERSON_URN', '')

    if not post_text:
        return 'Missing post_text — LinkedIn post not sent.'

    resp = requests.post(
        'https://api.linkedin.com/v2/ugcPosts',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'author': urn,
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {'text': post_text},
                    'shareMediaCategory': 'NONE',
                }
            },
            'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
        },
        timeout=15,
    )
    resp.raise_for_status()
    return f'LinkedIn post published. Status: {resp.status_code}'


def execute_post_facebook(details: dict, meta: dict) -> str:
    """Post to Facebook page."""
    post_text = details.get('post_text', '')
    page_id   = os.getenv('FACEBOOK_PAGE_ID', '')
    token     = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not post_text:
        return 'Missing post_text — Facebook post not sent.'

    resp = requests.post(
        f'https://graph.facebook.com/{page_id}/feed',
        data={'message': post_text, 'access_token': token},
        timeout=15,
    )
    resp.raise_for_status()
    return f'Facebook post published: {resp.json()}'


def execute_whatsapp_reply(details: dict, meta: dict) -> str:
    """Send WhatsApp reply via Business API."""
    reply_text = details.get('reply_text', '')
    phone      = details.get('to_phone', '')
    token      = os.getenv('WHATSAPP_API_TOKEN', '')
    phone_id   = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')

    if not reply_text or not phone:
        return 'Missing reply_text or to_phone — WhatsApp not sent.'

    resp = requests.post(
        f'https://graph.facebook.com/v18.0/{phone_id}/messages',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': reply_text},
        },
        timeout=15,
    )
    resp.raise_for_status()
    return f'WhatsApp reply sent to {phone}'


def execute_payment(details: dict, meta: dict) -> str:
    """Log payment approval. Actual transfer requires browser MCP."""
    amount    = details.get('amount', 'unknown')
    recipient = details.get('recipient', 'unknown')
    log.info('PAYMENT APPROVED: %s to %s — trigger browser MCP to complete transfer.', amount, recipient)
    return f'Payment logged: {amount} to {recipient}. Use browser MCP to complete.'


# Action dispatcher
ACTION_MAP = {
    'send_email':      execute_send_email,
    'post_linkedin':   execute_post_linkedin,
    'post_social':     execute_post_facebook,
    'whatsapp_reply':  execute_whatsapp_reply,
    'payment':         execute_payment,
}


# ── Main Processing ───────────────────────────────────────────────────────────

def process_approved(filepath: Path):
    """Execute an approved action file."""
    content  = filepath.read_text(encoding='utf-8')
    meta     = _extract_frontmatter(content)
    details  = _extract_json_block(content)
    action   = meta.get('action', 'unknown')

    log.info('Executing approved action: %s (%s)', action, filepath.name)

    executor = ACTION_MAP.get(action)
    if not executor:
        result = f'No executor for action type: {action}'
        log.warning(result)
        _audit(action, str(filepath), result, success=False)
        # Move to Done anyway to avoid reprocessing
        shutil.move(str(filepath), DONE / filepath.name)
        return

    try:
        result = executor(details, meta)
        log.info('Action succeeded: %s', result)
        _audit(action, str(filepath), result, success=True)
        # Archive to Done
        shutil.move(str(filepath), DONE / filepath.name)
        log.info('Archived to Done: %s', filepath.name)
    except Exception as exc:
        result = str(exc)
        log.error('Action failed: %s – %s', action, exc)
        _audit(action, str(filepath), result, success=False)
        # Move to Rejected on failure
        shutil.move(str(filepath), REJECTED / f'FAILED_{filepath.name}')


def process_rejected(filepath: Path):
    """Archive a rejected action file."""
    content = filepath.read_text(encoding='utf-8')
    meta    = _extract_frontmatter(content)
    action  = meta.get('action', 'unknown')
    log.info('Action rejected by human: %s (%s)', action, filepath.name)
    _audit(action, str(filepath), 'rejected_by_human', success=False)
    shutil.move(str(filepath), DONE / f'REJECTED_{filepath.name}')


def run():
    """Main loop — watch /Approved and /Rejected for files to process."""
    _ensure_folders()
    log.info('HITL Orchestrator started.')
    log.info('Watching: %s', VAULT_PATH)
    log.info('  /Approved  → execute action')
    log.info('  /Rejected  → log and archive')
    log.info('Move files from /Pending_Approval to /Approved or /Rejected to act.')

    while True:
        # Process approved actions
        for filepath in sorted(APPROVED.glob('*.md')):
            try:
                process_approved(filepath)
            except Exception as exc:
                log.error('Unexpected error processing %s: %s', filepath.name, exc)

        # Process rejected actions
        for filepath in sorted(REJECTED.glob('*.md')):
            if not filepath.name.startswith('REJECTED_') and not filepath.name.startswith('FAILED_'):
                try:
                    process_rejected(filepath)
                except Exception as exc:
                    log.error('Error archiving rejected file %s: %s', filepath.name, exc)

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    run()
