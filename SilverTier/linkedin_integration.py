"""
linkedin_integration.py – LinkedIn Auto-Post Integration (Silver Tier)
======================================================================
Uses LinkedIn OAuth2 API to:
  - Post text updates / articles to your LinkedIn profile
  - Queue posts for human approval before publishing
  - Read connection requests and save to Needs_Action

Architecture:
  Groq drafts post → saved to Vault/Pending_Approval/LINKEDIN_POST_*.md
  You move to /Approved → this script publishes it
  Result logged to Vault/Done/

Setup:
  1. Create LinkedIn Developer App at https://www.linkedin.com/developers/apps
  2. Add OAuth2 scopes: w_member_social, r_liteprofile, r_emailaddress
  3. Set LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN in .env
  4. Run: python linkedin_integration.py --setup  (first-time OAuth flow)
  5. Run: python linkedin_integration.py --post   (publish approved posts)
"""

import os
import re
import sys
import json
import logging
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "SilverTier" / ".env")
load_dotenv(Path(__file__).parent.parent / "BronzeTier" / ".env")

log = logging.getLogger("LinkedInIntegration")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LinkedIn] %(levelname)s %(message)s"
)

# ── Config ────────────────────────────────────────────────────────────────────

CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
ACCESS_TOKEN  = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
REDIRECT_URI  = "http://localhost:8080/callback"
VAULT_PATH    = Path(os.getenv("VAULT_PATH", "./Vault"))

LINKEDIN_API  = "https://api.linkedin.com/v2"
AUTH_URL      = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL     = "https://www.linkedin.com/oauth/v2/accessToken"
SCOPES        = ["w_member_social", "r_liteprofile", "r_emailaddress"]

TOKEN_FILE    = Path(__file__).parent / "linkedin_token.json"

# ── Token Management ──────────────────────────────────────────────────────────

def load_token() -> str:
    """Load access token from file or env."""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        return data.get("access_token", ACCESS_TOKEN)
    return ACCESS_TOKEN


def save_token(token_data: dict):
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    log.info("Token saved to %s", TOKEN_FILE)


def get_headers() -> dict:
    token = load_token()
    if not token:
        raise ValueError("No LinkedIn access token found. Run with --setup first.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

# ── OAuth2 Setup ──────────────────────────────────────────────────────────────

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        _OAuthCallbackHandler.auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")

    def log_message(self, *args):
        pass  # Suppress HTTP server logs


def setup_oauth():
    """Run OAuth2 authorization flow to get access token."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "linkedin_oauth_state",
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print("\n🔗 LinkedIn OAuth2 Setup")
    print("=" * 50)
    print("Opening browser for LinkedIn authorization...")
    webbrowser.open(auth_url)

    # Start local server to catch redirect
    server = HTTPServer(("localhost", 8080), _OAuthCallbackHandler)
    print("Waiting for authorization...")
    server.handle_request()

    code = _OAuthCallbackHandler.auth_code
    if not code:
        print("❌ Authorization failed — no code received.")
        sys.exit(1)

    # Exchange code for token
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    resp.raise_for_status()
    token_data = resp.json()
    save_token(token_data)

    print(f"\n✅ LinkedIn OAuth2 setup complete!")
    print(f"   Access token saved to: {TOKEN_FILE}")
    print(f"   Add to .env: LINKEDIN_ACCESS_TOKEN={token_data['access_token'][:20]}...")


# ── LinkedIn API ──────────────────────────────────────────────────────────────

def get_profile() -> dict:
    """Get current user's LinkedIn profile."""
    resp = requests.get(f"{LINKEDIN_API}/me", headers=get_headers())
    resp.raise_for_status()
    return resp.json()


def post_update(text: str, visibility: str = "PUBLIC") -> dict:
    """Post a text update to LinkedIn profile."""
    profile = get_profile()
    person_urn = f"urn:li:person:{profile['id']}"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        },
    }

    resp = requests.post(
        f"{LINKEDIN_API}/ugcPosts",
        headers=get_headers(),
        json=payload,
    )
    resp.raise_for_status()
    result = resp.json()
    log.info("Posted to LinkedIn: %s", result.get("id", "unknown"))
    return result


# ── Draft Post (for HITL approval) ───────────────────────────────────────────

def draft_post(topic: str, content: str) -> Path:
    """
    Draft a LinkedIn post and save to Vault/Pending_Approval for human review.
    Uses Groq to generate the post content.
    """
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""Write a professional LinkedIn post about the following topic.
Keep it engaging, under 1300 characters, use 2-3 relevant emojis, end with a question or call-to-action.

Topic: {topic}
Additional context: {content}

Output ONLY the post text, nothing else."""

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    post_text = response.choices[0].message.content.strip()

    # Save to Pending_Approval for HITL
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    filepath = pending_dir / f"LINKEDIN_POST_{timestamp}.md"
    filepath.write_text(f"""---
type: approval_request
action: linkedin_post
topic: {topic}
created: {datetime.now().isoformat()}
status: pending
visibility: PUBLIC
---

## Drafted LinkedIn Post

{post_text}

---

## To Approve
Move this file to /Approved folder.
The post will be published automatically.

## To Edit
Edit the post text above, then move to /Approved.

## To Reject
Move this file to /Rejected folder.
""", encoding="utf-8")

    log.info("LinkedIn post draft saved: %s", filepath.name)
    print(f"\n✅ Draft saved to: {filepath}")
    print("   Move to Vault/Approved/ to publish, or Vault/Rejected/ to discard.")
    return filepath


# ── Process Approved Posts ────────────────────────────────────────────────────

def process_approved_posts():
    """Watch Vault/Approved/ for LINKEDIN_POST_*.md files and publish them."""
    approved_dir = VAULT_PATH / "Approved"
    done_dir = VAULT_PATH / "Done"
    done_dir.mkdir(parents=True, exist_ok=True)

    posts = list(approved_dir.glob("LINKEDIN_POST_*.md"))
    if not posts:
        log.info("No approved LinkedIn posts found.")
        return

    for post_file in posts:
        try:
            content = post_file.read_text(encoding="utf-8")

            # Extract post text (between ## Drafted LinkedIn Post and ---)
            match = re.search(
                r"## Drafted LinkedIn Post\s*\n(.*?)\n---",
                content, re.DOTALL
            )
            if not match:
                log.warning("Could not extract post text from %s", post_file.name)
                continue

            post_text = match.group(1).strip()

            # Extract visibility
            vis_match = re.search(r"^visibility:\s*(\w+)", content, re.MULTILINE)
            visibility = vis_match.group(1) if vis_match else "PUBLIC"

            # Publish
            log.info("Publishing LinkedIn post from %s...", post_file.name)
            result = post_update(post_text, visibility)
            post_id = result.get("id", "unknown")

            # Move to Done with updated status
            updated = content.replace("status: pending", "status: published")
            updated += f"\n\n## Published\n- Post ID: {post_id}\n- Published: {datetime.now().isoformat()}\n"
            done_path = done_dir / f"PUBLISHED_{post_file.name}"
            done_path.write_text(updated, encoding="utf-8")
            post_file.unlink()

            log.info("✅ Published! Post ID: %s → moved to Done/", post_id)
            print(f"\n✅ LinkedIn post published!")
            print(f"   Post ID: {post_id}")
            print(f"   View at: https://www.linkedin.com/feed/")

        except Exception as e:
            log.error("Failed to publish %s: %s", post_file.name, e)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Integration for AI Employee")
    parser.add_argument("--setup", action="store_true", help="Run OAuth2 setup flow")
    parser.add_argument("--profile", action="store_true", help="Show LinkedIn profile")
    parser.add_argument("--draft", metavar="TOPIC", help="Draft a post on a topic (requires Groq)")
    parser.add_argument("--publish", action="store_true", help="Publish all approved posts from Vault/Approved/")
    parser.add_argument("--post", metavar="TEXT", help="Post directly (no approval, use carefully)")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./Vault"), help="Vault path")
    args = parser.parse_args()

    VAULT_PATH = Path(args.vault)

    if args.setup:
        setup_oauth()

    elif args.profile:
        profile = get_profile()
        print(f"\n👤 LinkedIn Profile")
        print(f"   Name: {profile.get('localizedFirstName')} {profile.get('localizedLastName')}")
        print(f"   ID:   {profile.get('id')}")

    elif args.draft:
        draft_post(topic=args.draft, content="")

    elif args.publish:
        process_approved_posts()

    elif args.post:
        result = post_update(args.post)
        print(f"✅ Posted! ID: {result.get('id')}")

    else:
        parser.print_help()
