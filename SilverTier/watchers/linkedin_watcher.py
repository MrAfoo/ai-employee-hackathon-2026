"""
LinkedIn Watcher – polls LinkedIn notifications and messages via the
LinkedIn API and writes notes to the Obsidian vault Inbox.

Requires: LinkedIn OAuth2 access token with r_liteprofile + r_emailaddress
+ w_member_social scopes.

See: https://learn.microsoft.com/en-us/linkedin/shared/authentication/
"""
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LinkedInWatcher] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInWatcher:
    """
    Polls LinkedIn for new notifications and connection requests,
    writing a Markdown note to the vault Inbox for each event found.
    """

    def __init__(
        self,
        vault_path: str,
        access_token: str | None = None,
        poll_interval: int | None = None,
    ):
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.poll_interval = poll_interval or int(os.getenv("WATCHER_POLL_INTERVAL", "300"))
        self._seen_ids: set[str] = set()

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def _get_profile(self) -> dict:
        """Fetch current user's basic profile."""
        resp = requests.get(
            f"{LINKEDIN_API_BASE}/me",
            headers=self._headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _get_notifications(self) -> list[dict]:
        """
        Fetch recent notifications. Returns simplified list of events.
        Note: Full notification API requires LinkedIn partner access.
        This uses the /socialActions endpoint as a proxy for engagement.
        """
        resp = requests.get(
            f"{LINKEDIN_API_BASE}/socialMetadata",
            headers=self._headers,
            timeout=15,
        )
        if resp.status_code == 403:
            log.warning("LinkedIn notification API requires partner access. Using profile ping instead.")
            return []
        resp.raise_for_status()
        return resp.json().get("elements", [])

    def _get_connection_requests(self) -> list[dict]:
        """Fetch pending connection invitations."""
        resp = requests.get(
            f"{LINKEDIN_API_BASE}/invitations?invitationTypes=List(CONNECTION)",
            headers=self._headers,
            timeout=15,
        )
        if resp.status_code in (403, 404):
            log.warning("Connection invitation API not available with current permissions.")
            return []
        resp.raise_for_status()
        return resp.json().get("elements", [])

    def _write_note(self, title: str, body: str, source: str = "linkedin"):
        inbox = self.vault_path / "Inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60]
        note_file = inbox / f"{timestamp}_linkedin_{safe_title}.md"
        content = f"""---
title: "{title}"
created: {datetime.now().isoformat()}
source: {source}
tags: [inbox, linkedin]
---

# {title}

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{body}
"""
        note_file.write_text(content, encoding="utf-8")
        log.info("Note written: %s", note_file.name)

    def _poll_once(self):
        notifications = self._get_notifications()
        for n in notifications:
            nid = str(n.get("id", ""))
            if nid and nid not in self._seen_ids:
                self._seen_ids.add(nid)
                event_type = n.get("type", "notification")
                actor = n.get("actor", {}).get("name", "Unknown")
                detail = n.get("message", {}).get("text", str(n))
                self._write_note(
                    title=f"LinkedIn {event_type} from {actor}",
                    body=f"**Event:** {event_type}\n**Actor:** {actor}\n\n{detail}",
                )

        invites = self._get_connection_requests()
        for inv in invites:
            iid = str(inv.get("entityUrn", inv.get("id", "")))
            if iid and iid not in self._seen_ids:
                self._seen_ids.add(iid)
                from_name = inv.get("fromMember", {}).get("firstName", {}).get("localized", {})
                from_name = list(from_name.values())[0] if from_name else "Unknown"
                message = inv.get("message", "No message.")
                self._write_note(
                    title=f"LinkedIn Connection Request from {from_name}",
                    body=f"**From:** {from_name}\n**Message:** {message}",
                    source="linkedin_invite",
                )

    def run(self):
        if not self.access_token:
            log.error("LINKEDIN_ACCESS_TOKEN must be set in .env")
            return
        log.info("LinkedIn watcher started (poll every %ds)", self.poll_interval)
        while True:
            try:
                self._poll_once()
            except requests.RequestException as exc:
                log.error("LinkedIn API error: %s – retrying in 60s", exc)
                time.sleep(60)
                continue
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    vault = os.getenv("VAULT_PATH", "./BronzeTier")
    watcher = LinkedInWatcher(vault_path=vault)
    watcher.run()
