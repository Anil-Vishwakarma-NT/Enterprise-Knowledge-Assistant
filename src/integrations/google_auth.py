"""
Shared Google OAuth 2.0 helper for Gmail + Calendar.

Both tools request their scopes together in ONE consent flow, so the
user only approves access once instead of twice.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from src.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

# Combined scopes: send-only Gmail access + read-only Calendar access.
# Neither tool can read your inbox or modify/delete calendar events.
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_google_credentials() -> Credentials:
    """Returns valid OAuth credentials, running the browser consent flow
    once and caching/refreshing the token on every call after that."""
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Google OAuth client file not found at '{GMAIL_CREDENTIALS_PATH}'. "
                    "Download it from Google Cloud Console (OAuth client ID -> "
                    "Desktop app) and place it there. See README.md 'Google setup'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(GMAIL_TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds
