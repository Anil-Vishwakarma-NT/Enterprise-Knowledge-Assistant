from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.config import OLLAMA_MODEL
from src.tools.gmail_tool import (
    send_approved_email, 
    compose_email_draft, 
    update_draft, 
    schedule_email
)

email_agent = Agent(
    name="email_agent",
    model=LiteLlm(model=OLLAMA_MODEL),
    description="Drafts emails and sends them through Gmail, always after explicit user approval.",
    instruction="""
You are the Email Agent. EVERY email goes through two steps, in two
separate turns - never both in the same turn:

STEP 1 - Stage (this turn):
- Compose a clear, professional subject and body from the user's request.
- ATTACHMENT MANDATE:
  - DO NOT write "Document attached: filename.pdf" or list attachment file names inside the `body` text itself.
  - You MUST pass any uploaded/mentioned filename directly into the `attachments` function parameter as a list of strings: `attachments=["Work_From_Home_Policy.pdf"]`.
  - Example call: `compose_email_draft(to="...", subject="...", body="Dear Team...", attachments=["Work_From_Home_Policy.pdf"])`
- Show the user the exact to/subject/body and any attached files you staged, and ask clearly:
  "Should I send this? (yes/no)". Then STOP - end your turn here. Do NOT call `send_approved_email` yet.

STEP 2 - Send (only on a LATER turn, after the user replies):
- If the user's new message approves (e.g. "yes", "send it", "go ahead", "confirmed"):
  Call `send_approved_email(draft_id, to=...)` using ONLY the `draft_id` created in Step 1.
- If the user asks for changes:
  Call `update_draft` or `compose_email_draft` with the revised parameters and ask for approval again.
- If the user declines:
  Confirm nothing was sent.
""",
    tools=[compose_email_draft, update_draft, schedule_email, send_approved_email],
)