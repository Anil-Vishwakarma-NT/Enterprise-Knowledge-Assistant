"""
Handles Google OAuth2 authentication for Gmail and Calendar APIs.

First run: opens a browser window for you to log in and grant consent.
After that: reuses the cached token file, so you won't be prompted again
until it expires or is revoked.
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes requested. If you change these, delete the token file and re-auth.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

# Resolve paths relative to the project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS_PATH = Path(
    os.getenv("GOOGLE_CREDENTIALS_PATH", PROJECT_ROOT / "credentials" / "credentials.json")
)
TOKEN_PATH = Path(
    os.getenv("GOOGLE_TOKEN_PATH", PROJECT_ROOT / "credentials" / "token.json")
)

_gmail_service = None
_calendar_service = None


def _get_credentials() -> Credentials:
    """Loads cached credentials, refreshes them, or runs the OAuth flow."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing OAuth client file at {CREDENTIALS_PATH}.\n"
                    "Download it from Google Cloud Console > APIs & Services > "
                    "Credentials > OAuth Client ID (Desktop app) and save it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def get_gmail_service():
    """Returns a cached, authenticated Gmail API client."""
    global _gmail_service
    if _gmail_service is None:
        creds = _get_credentials()
        _gmail_service = build("gmail", "v1", credentials=creds)
    return _gmail_service


def get_calendar_service():
    """Returns a cached, authenticated Calendar API client."""
    global _calendar_service
    if _calendar_service is None:
        creds = _get_credentials()
        _calendar_service = build("calendar", "v3", credentials=creds)
    return _calendar_service
