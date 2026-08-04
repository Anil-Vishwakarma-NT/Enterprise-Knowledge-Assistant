"""
FR-5: Tool Calling - Real Gmail sending & draft management via Gmail API.
By design, emails can ONLY be sent if they exist in staged storage (pending_approval).
Directly sending arbitrary text without a staged draft ID is restricted.
"""

import base64
import json
import os
import shutil
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from googleapiclient.discovery import build

from src.config import GMAIL_SENDER_LABEL, EMAIL_DRAFTS_PATH, BASE_DIR, DATA_DIR
from auth.google_auth import get_gmail_service


# ---------------------------------------------------------------------------
# Storage Helpers
# ---------------------------------------------------------------------------

def _load_drafts() -> list[dict]:
    if os.path.exists(EMAIL_DRAFTS_PATH):
        with open(EMAIL_DRAFTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_drafts(drafts: list[dict]) -> None:
    os.makedirs(os.path.dirname(EMAIL_DRAFTS_PATH), exist_ok=True)
    with open(EMAIL_DRAFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)


def get_draft(draft_id: str) -> dict | None:
    """Internal helper to fetch a staged draft by its ID."""
    for d in _load_drafts():
        if d["id"] == draft_id:
            return d
    return None


def mark_draft_sent(draft_id: str, message_id: str) -> None:
    """Internal helper - updates draft status to 'sent' once delivered."""
    drafts = _load_drafts()
    for d in drafts:
        if d["id"] == draft_id:
            d["status"] = "sent"
            d["gmail_message_id"] = message_id
            d["sent_at"] = datetime.now(timezone.utc).isoformat()
    _save_drafts(drafts)


def _resolve_and_save_attachment(file_path: str) -> str | None:
    """Dynamically catches uploaded UI files, copies them to the ./data/ directory, 
    and returns the resolved path from ./data/.
    """
    if not file_path:
        return None

    input_path = Path(file_path)
    filename = input_path.name

    # Ensure the destination data directory exists
    target_data_dir = Path(DATA_DIR)
    target_data_dir.mkdir(parents=True, exist_ok=True)
    destination_file = target_data_dir / filename

    # 1. If file is directly accessible at input_path
    if input_path.is_file():
        if input_path.resolve() != destination_file.resolve():
            shutil.copy2(input_path, destination_file)
        return str(destination_file.resolve())

    # 2. Search common ADK UI upload, session, workspace, and artifact locations
    search_dirs = [
        Path(BASE_DIR),
        Path(BASE_DIR) / "artifacts",
        Path(BASE_DIR) / ".adk",
        Path(BASE_DIR) / "adk_app",
        Path(BASE_DIR) / "data",
        Path(os.getcwd()),
    ]

    for directory in search_dirs:
        if directory.exists():
            matched = list(directory.rglob(filename))
            if matched:
                source_file = matched[0]
                # Automatically copy the caught uploaded file into ./data/
                if source_file.resolve() != destination_file.resolve():
                    shutil.copy2(source_file, destination_file)
                return str(destination_file.resolve())

    return None


# ---------------------------------------------------------------------------
# Agent Tools: Compose, Update, Schedule
# ---------------------------------------------------------------------------

def compose_email_draft(
    to: str, 
    subject: str, 
    body: str, 
    attachments: list[str] | None = None
) -> dict:
    """Stage an email draft for user approval.
    
    This NEVER sends an email immediately. It saves a pending draft and returns 
    it for review. You MUST show the details to the user and explicitly ask for 
    approval before calling send_approved_email.
    Args:
        to: Recipient email address.
        subject: Subject line of the email.
        body: Body of the email (plain text or markdown).
        attachments: Optional list of local file paths or filenames to attach.
    Returns:
        dict containing draft_id, status "pending_approval", and staged contents.
    """
    drafts = _load_drafts()
    draft_id = f"DRAFT-{len(drafts) + 1:04d}"

    valid_attachments = []
    missing_attachments = []

    if attachments:
        for att in attachments:
            resolved = _resolve_and_save_attachment(att)
            if resolved:
                valid_attachments.append(resolved)
            else:
                missing_attachments.append(att)

    draft = {
        "id": draft_id,
        "to": to,
        "subject": subject,
        "body": body,
        "attachments": valid_attachments,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scheduled_for": None,
    }
    drafts.append(draft)
    _save_drafts(drafts)

    result = {
        "draft_id": draft_id,
        "status": "pending_approval",
        "to": to,
        "subject": subject,
        "body": body,
        "attached_files": [Path(p).name for p in valid_attachments],
    }
    if missing_attachments:
        result["warning"] = f"Could not locate these attachment files on disk: {missing_attachments}"

    return result


def update_draft(
    draft_id: str,
    to: str | None = None,
    subject: str | None = None,
    body: str | None = None,
    attachments: list[str] | None = None,
) -> dict:
    """Modify an existing staged draft before it is sent.
    Args:
        draft_id: The ID of the draft to update (e.g., "DRAFT-0001").
        to: New recipient email address (optional).
        subject: New subject line (optional).
        body: New email body text (optional).
        attachments: Updated list of local file paths or filenames (optional).
    Returns:
        dict with updated draft details or an error message.
    """
    drafts = _load_drafts()
    for d in drafts:
        if d["id"] == draft_id:
            if d["status"] == "sent":
                return {"status": "error", "error": f"Draft {draft_id} has already been sent and cannot be edited."}

            if to is not None:
                d["to"] = to
            if subject is not None:
                d["subject"] = subject
            if body is not None:
                d["body"] = body
            if attachments is not None:
                resolved_list = []
                for att in attachments:
                    res = _resolve_and_save_attachment(att)
                    if res:
                        resolved_list.append(res)
                d["attachments"] = resolved_list

            d["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_drafts(drafts)
            return {"status": "updated", "draft_id": draft_id, "updated_draft": d}

    return {"status": "error", "error": f"Draft '{draft_id}' not found."}


def schedule_email(draft_id: str, send_at_iso: str) -> dict:
    """Schedule a staged draft to be sent at a future time.
    Args:
        draft_id: The ID of the staged draft (e.g., "DRAFT-0001").
        send_at_iso: ISO 8601 formatted timestamp string (e.g., "2026-08-01T09:00:00Z").
    Returns:
        dict indicating whether scheduling was successful.
    """
    drafts = _load_drafts()
    for d in drafts:
        if d["id"] == draft_id:
            if d["status"] == "sent":
                return {"status": "error", "error": f"Draft {draft_id} was already sent."}

            try:
                scheduled_dt = datetime.fromisoformat(send_at_iso.replace("Z", "+00:00"))
                d["scheduled_for"] = scheduled_dt.isoformat()
                d["status"] = "scheduled"
                _save_drafts(drafts)
                return {
                    "status": "scheduled", 
                    "draft_id": draft_id, 
                    "scheduled_for": d["scheduled_for"]
                }
            except ValueError:
                return {"status": "error", "error": "Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ"}

    return {"status": "error", "error": f"Draft '{draft_id}' not found."}


# ---------------------------------------------------------------------------
# Sending & MIME Construction
# ---------------------------------------------------------------------------

def _build_mime_message(
    sender: str, 
    to: str, 
    subject: str, 
    body_text: str, 
    attachments: list[str] | None = None
) -> MIMEMultipart:
    """Constructs a standard MIME multipart message with text body and attachments."""
    # Top-level container must be multipart/mixed
    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    # Create the text container (multipart/alternative)
    msg_body = MIMEMultipart("alternative")
    msg_body.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(msg_body)

    # Attach Files
    if attachments:
        for file_path in attachments:
            if not file_path or not os.path.exists(file_path):
                continue

            content_type, encoding = mimetypes.guess_type(file_path)
            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"

            main_type, sub_type = content_type.split("/", 1)

            with open(file_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())

            encoders.encode_base64(part)
            filename = os.path.basename(file_path)

            # Explicitly state Content-Disposition with header parameters
            part.add_header(
                "Content-Disposition", 
                "attachment", 
                filename=filename
            )
            msg.attach(part)

    return msg


def send_approved_email(draft_id: str, to: str | None = None) -> dict:
    """Send a staged email draft after explicit user approval.
    Args:
        draft_id: The ID returned by compose_email_draft, e.g. "DRAFT-0001".
        to: Optional recipient override if the user provided a new address during approval.
    Returns:
        dict with status "sent" and the Gmail message ID, or an error status.
    """
    draft = get_draft(draft_id)
    if not draft:
        return {"status": "error", "error": f"No staged draft found with id '{draft_id}'."}
    if draft["status"] == "sent":
        return {"status": "error", "error": f"Draft {draft_id} was already sent."}

    # Resolve final recipient (use override if provided, else fall back to draft recipient)
    recipient = to if to else draft["to"]

    try:
        service = get_gmail_service()

        mime_msg = _build_mime_message(
            sender=GMAIL_SENDER_LABEL,
            to=recipient,
            subject=draft["subject"],
            body_text=draft["body"],
            attachments=draft.get("attachments", [])
        )

        raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

        sent = (
            service.users()
            .messages()
            .send(userId=GMAIL_SENDER_LABEL, body={"raw": raw})
            .execute()
        )

        mark_draft_sent(draft_id, sent.get("id"))
        return {
            "status": "sent", 
            "message_id": sent.get("id"), 
            "to": recipient, 
            "subject": draft["subject"],
            "attachments_sent": [os.path.basename(p) for p in draft.get("attachments", [])]
        }

    except FileNotFoundError as e:
        return {"status": "error", "error": f"Credentials file missing: {e}"}
    except Exception as e:
        return {"status": "error", "error": f"Failed to send email via Gmail API: {e}"}