"""
whatsapp_watcher.py – Read-Only WhatsApp Web Monitor (Playwright)
=================================================================
Watches WhatsApp Web for incoming messages matching urgent keywords.
Creates Needs_Action .md files for the Orchestrator to process.

NEVER sends messages automatically — read only, HITL safeguard.

First-time setup (scan QR code):
    python whatsapp_watcher.py --setup

Normal run (headless, background):
    python whatsapp_watcher.py
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from base_watcher import BaseWatcher
except ImportError:
    from watchers.base_watcher import BaseWatcher

log = logging.getLogger("WhatsAppWatcher")

KEYWORDS = [
    "urgent", "asap", "invoice", "payment", "help",
    "emergency", "deadline", "overdue", "important", "please reply"
]

_DEFAULT_SESSION = Path(__file__).resolve().parent.parent.parent / "whatsapp_session"
SESSION_PATH = Path(os.getenv("WHATSAPP_SESSION_PATH", str(_DEFAULT_SESSION))).resolve()


class WhatsAppWatcher(BaseWatcher):
    """Read-only WhatsApp Web watcher using Playwright persistent context."""

    def __init__(self, vault_path: str, headless: bool = True):
        super().__init__(vault_path, check_interval=30)
        self.headless = headless
        self.session_path = SESSION_PATH
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.processed_ids: set = set()

    # ── BaseWatcher interface ─────────────────────────────────────────────────

    def check_for_updates(self) -> list:
        """Open WhatsApp Web, scrape unread urgent messages, return list."""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError:
            log.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return []

        messages = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    ],
                    ignore_default_args=["--enable-automation"],
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

                # Wait for page to load fully
                time.sleep(5)

                # Try multiple selectors — WhatsApp Web changes these frequently
                logged_in = False
                login_selectors = [
                    '[data-testid="chat-list"]',
                    '#pane-side',
                    'div[aria-label="Chat list"]',
                    '[data-testid="cell-frame-container"]',
                ]
                for sel in login_selectors:
                    try:
                        page.wait_for_selector(sel, timeout=15000)
                        logged_in = True
                        log.info("WhatsApp Web logged in (selector: %s)", sel)
                        break
                    except PWTimeout:
                        continue

                if not logged_in:
                    # Last resort: check page title
                    title = page.title()
                    log.info("Page title: %s", title)
                    if "whatsapp" in title.lower():
                        logged_in = True
                        log.info("WhatsApp Web logged in (title check)")
                    else:
                        log.warning("WhatsApp Web not logged in. Run with --setup to scan QR.")
                        browser.close()
                        return []

                # Find chats with unread badge
                unread_chats = page.query_selector_all('[data-testid="cell-frame-container"]')
                for chat in unread_chats:
                    try:
                        badge = chat.query_selector('[data-testid="icon-unread-count"]')
                        if not badge:
                            continue

                        # Get contact name
                        name_el = chat.query_selector('[data-testid="cell-frame-title"]')
                        name = name_el.inner_text().strip() if name_el else "Unknown"

                        # Get last message snippet
                        snippet_el = chat.query_selector('[data-testid="last-msg-status"] ~ span, '
                                                          '[data-testid="cell-frame-secondary-detail"] span')
                        snippet = snippet_el.inner_text().strip() if snippet_el else ""

                        # Only process if keyword matches
                        if not any(kw in snippet.lower() for kw in KEYWORDS):
                            continue

                        msg_id = f"{name}_{hash(snippet)}"
                        if msg_id in self.processed_ids:
                            continue

                        messages.append({
                            "id": msg_id,
                            "contact": name,
                            "snippet": snippet,
                            "timestamp": datetime.now().isoformat(),
                        })
                    except Exception as e:
                        log.debug("Error parsing chat: %s", e)
                        continue

                browser.close()
        except Exception as e:
            log.error("WhatsApp check failed: %s", e)

        return messages

    def create_action_file(self, item: dict) -> Path:
        """Write a Needs_Action .md file for the message."""
        safe_name = item["contact"].replace(" ", "_").replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.needs_action / f"WHATSAPP_{safe_name}_{timestamp}.md"

        content = f"""---
type: whatsapp
contact: {item['contact']}
received: {item['timestamp']}
priority: high
status: pending
source: whatsapp_web_readonly
---

## Message Preview
{item['snippet']}

## ⚠️ Read-Only Mode
This agent does NOT auto-reply to WhatsApp messages.
Review Plan.md for suggested reply, then send manually.

## Suggested Actions
- [ ] Review message from {item['contact']}
- [ ] Check Plan.md for suggested reply
- [ ] Reply manually in WhatsApp
"""
        filepath.write_text(content, encoding="utf-8")
        self.processed_ids.add(item["id"])
        self.logger.info("Created: %s", filepath.name)
        return filepath


def setup_session(vault_path: str):
    """First-time setup: open WhatsApp Web with visible browser to scan QR."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("\n📱 WhatsApp Web QR Setup")
    print("=" * 50)
    print(f"Session will be saved to: {SESSION_PATH}")
    print("\n1. A browser window will open")
    print("2. Scan the QR code with your WhatsApp app")
    print("   (WhatsApp → Settings → Linked Devices → Link a Device)")
    print("3. Wait for chats to load")
    print("4. Close the browser window")
    print("\nOpening browser...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(SESSION_PATH),
            headless=False,
            args=["--no-sandbox"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://web.whatsapp.com")
        print("✅ Browser opened. Scan the QR code now.")
        print("   Waiting up to 3 minutes for chats to load...")
        print("   DO NOT close the browser — wait until your chats appear.")

        # Try multiple selectors — WhatsApp Web changes data-testid frequently
        selectors = [
            '[data-testid="chat-list"]',
            '#pane-side',
            'div[aria-label="Chat list"]',
            '._3YS_f',  # fallback class
        ]
        logged_in = False
        try:
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=180000)
                    logged_in = True
                    break
                except Exception:
                    continue

            if logged_in:
                print("\n✅ QR scan successful! Chats loaded.")
                print(f"   Session stored at: {SESSION_PATH}")
                print("   Waiting 5 seconds to ensure session is fully saved...")
                time.sleep(5)
                print("✅ Setup complete! You can now close the browser.")
                print("   Run without --setup to start monitoring.")
                input("   Press ENTER to close the browser and exit...")
            else:
                print("\n⚠️  Could not detect chat list automatically.")
                print("   If your chats are visible in the browser, the session IS saved.")
                input("   Press ENTER when your chats are visible to save session and exit...")
                print("✅ Session saved.")
        except KeyboardInterrupt:
            print("\n✅ Session saved (Ctrl+C detected).")
            print("   If chats were visible, run without --setup to start monitoring.")
        finally:
            try:
                browser.close()
            except Exception:
                pass  # Browser may already be closed — that's fine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhatsApp Web Read-Only Watcher")
    parser.add_argument("--setup", action="store_true", help="Scan QR code (first-time setup)")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./Vault"), help="Vault path")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [WhatsAppWatcher] %(levelname)s %(message)s",
    )

    if args.setup:
        setup_session(args.vault)
    else:
        watcher = WhatsAppWatcher(vault_path=args.vault)
        watcher.check_interval = args.interval
        print(f"🟢 WhatsApp Watcher started (read-only, interval={args.interval}s)")
        print(f"   Vault: {args.vault}")
        print(f"   Session: {SESSION_PATH}")
        print("   Watching for urgent keywords in unread messages...")
        watcher.run()
