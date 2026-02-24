"""
setup_gmail_oauth.py – One-time Gmail OAuth2 setup helper.

Run this ONCE to authenticate with Gmail and generate credentials.json + token.json.
After that, GmailWatcher will use these files automatically.

Steps:
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable Gmail API
  3. Create OAuth2 credentials (Desktop App) → Download as credentials.json
  4. Place credentials.json in BronzeTier/ folder
  5. Run: python setup_gmail_oauth.py
  6. Browser opens → sign in → grant access
  7. token.json is saved — GmailWatcher is now ready!

Usage:
  python setup_gmail_oauth.py
  python setup_gmail_oauth.py --credentials path/to/credentials.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("❌ Missing Google libraries. Run:")
    print("   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',    # Read emails
    'https://www.googleapis.com/auth/gmail.send',        # Send emails
    'https://www.googleapis.com/auth/gmail.modify',      # Mark as read
]


def setup_oauth(credentials_path: Path, token_path: Path):
    creds = None

    # Load existing token if available
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing existing token...")
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print(f"❌ credentials.json not found at: {credentials_path}")
                print()
                print("How to get credentials.json:")
                print("  1. Go to https://console.cloud.google.com")
                print("  2. Create/select a project")
                print("  3. Go to APIs & Services → Library → search 'Gmail API' → Enable")
                print("  4. Go to APIs & Services → Credentials")
                print("  5. Click 'Create Credentials' → OAuth client ID")
                print("  6. Application type: Desktop app → Create")
                print("  7. Download JSON → rename to credentials.json")
                print(f"  8. Place in: {credentials_path.parent}/")
                sys.exit(1)

            print("🌐 Opening browser for Gmail authentication...")
            print("   Sign in with your Gmail account and grant the requested permissions.")
            print()
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future use
        token_path.write_text(creds.to_json(), encoding='utf-8')
        print(f"✅ Token saved to: {token_path}")

    # Test the connection
    print("\n🔍 Testing Gmail connection...")
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    email = profile.get('emailAddress', 'unknown')
    total = profile.get('messagesTotal', 0)

    print(f"✅ Connected to Gmail: {email}")
    print(f"   Total messages: {total:,}")

    # Test fetching unread important emails
    results = service.users().messages().list(
        userId='me', q='is:unread is:important', maxResults=5
    ).execute()
    unread = results.get('messages', [])
    print(f"   Unread important: {len(unread)}")

    print()
    print("=" * 50)
    print("✅ Gmail OAuth2 setup complete!")
    print(f"   credentials.json : {credentials_path}")
    print(f"   token.json       : {token_path}")
    print()
    print("Next: Update your .env file:")
    print(f"   GMAIL_CREDENTIALS_PATH={credentials_path}")
    print(f"   GMAIL_TOKEN_PATH={token_path}")
    print()
    print("Then run: python Orchestrator.py")

    return creds


def main():
    parser = argparse.ArgumentParser(description='Gmail OAuth2 Setup for AI Employee')
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to credentials.json downloaded from Google Cloud Console'
    )
    parser.add_argument(
        '--token',
        default='token.json',
        help='Path to save the token.json file'
    )
    args = parser.parse_args()

    credentials_path = Path(args.credentials).resolve()
    token_path = Path(args.token).resolve()

    print("🔐 Gmail OAuth2 Setup for AI Employee")
    print("=" * 50)
    print(f"Credentials: {credentials_path}")
    print(f"Token output: {token_path}")
    print()

    setup_oauth(credentials_path, token_path)


if __name__ == '__main__':
    main()
