"""
gmail_watcher.py – Gmail Watcher using Google OAuth2 + Gmail API.

Uses the official Google API (not IMAP) with OAuth2 credentials.
Monitors unread important emails and writes .md notes to /Needs_Action.

Setup:
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable Gmail API
  3. Create OAuth2 credentials (Desktop App) → Download as credentials.json
  4. Set GMAIL_CREDENTIALS_PATH=./credentials.json in .env
  5. First run will open browser for OAuth consent → saves token.json
  6. Set GMAIL_TOKEN_PATH=./token.json in .env
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    from base_watcher import BaseWatcher
except ImportError:
    from watchers.base_watcher import BaseWatcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [GmailWatcher] %(levelname)s %(message)s',
)

# Gmail API scope — read-only is enough for watching
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str | None = None):
        super().__init__(vault_path, check_interval=120)
        self.credentials_path = Path(
            credentials_path or os.getenv('GMAIL_CREDENTIALS_PATH', './credentials.json')
        )
        self.token_path = Path(os.getenv('GMAIL_TOKEN_PATH', './token.json'))
        self.processed_ids: set[str] = set()
        self.service = self._authenticate()

    def _authenticate(self):
        """Authenticate with Google OAuth2 and return Gmail API service."""
        creds = None

        # Load existing token
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # Refresh or re-authenticate if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info('Refreshing Gmail OAuth2 token...')
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f'Gmail credentials not found at {self.credentials_path}.\n'
                        'Download from Google Cloud Console → APIs & Services → Credentials.'
                    )
                self.logger.info('Opening browser for Gmail OAuth2 consent...')
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next run
            self.token_path.write_text(creds.to_json(), encoding='utf-8')
            self.logger.info('Token saved to %s', self.token_path)

        service = build('gmail', 'v1', credentials=creds)
        self.logger.info('Gmail API authenticated successfully.')
        return service

    def check_for_updates(self) -> list:
        """Return list of unread important messages not yet processed."""
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread is:important',
            maxResults=20,
        ).execute()
        messages = results.get('messages', [])
        new = [m for m in messages if m['id'] not in self.processed_ids]
        self.logger.info('Found %d new unread important emails.', len(new))
        return new

    def create_action_file(self, message: dict) -> Path:
        """Fetch full message and write .md note to /Needs_Action."""
        msg = self.service.users().messages().get(
            userId='me',
            id=message['id'],
            format='full',
        ).execute()

        # Extract headers
        headers = {
            h['name']: h['value']
            for h in msg.get('payload', {}).get('headers', [])
        }
        subject  = headers.get('Subject', '(no subject)')
        sender   = headers.get('From', 'Unknown')
        date_str = headers.get('Date', datetime.now().isoformat())
        snippet  = msg.get('snippet', '')

        content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: high
status: pending
message_id: {message['id']}
---

# 📧 Email: {subject}

**From:** {sender}
**Subject:** {subject}
**Received:** {date_str}

## Email Content
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
        filepath = self.needs_action / f'EMAIL_{message["id"]}.md'
        filepath.write_text(content, encoding='utf-8')
        self.processed_ids.add(message['id'])
        return filepath


if __name__ == '__main__':
    vault = os.getenv('VAULT_PATH', './BronzeTier/Vault')
    watcher = GmailWatcher(vault_path=vault)
    watcher.run()
