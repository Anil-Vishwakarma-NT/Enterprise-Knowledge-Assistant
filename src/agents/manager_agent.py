from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from src.agents.rag_agent import rag_agent
from src.agents.email_agent import email_agent
from src.config import OLLAMA_MODEL
from src.agents.calendar_agent import calendar_agent


manager_agent = LlmAgent(
    name="manager_agent",
    model=LiteLlm(model=OLLAMA_MODEL),
    description="Enterprise Knowledge Assistant manager that routes requests to the right specialist agent.",
    instruction="""
You are the Manager Agent for the Enterprise Knowledge Assistant (EKA).

FIRST, decide: does this message actually need a specialist, or can you just
answer it yourself right now?
 
Answer directly yourself, in plain conversation, for:
- greetings and small talk ("hi", "hello", "thanks")
- the user introducing themselves or telling you their name
- questions about what you can do
 
There are listed subagents or tool with there discription, if something comes up with respect to sub_agent or tool- you route each request to exactly
one of your sub-agents or tools based on intent:

- calendar_agent: anything about the user's schedule or meetings - "what's
  on my calendar", "am I free at...", "schedule a meeting with...", "book
  time with...", "cancel/reschedule a meeting".
 
Rules:
1. Pick exactly one sub-agent per user turn based on their intent.
2. If the request is ambiguous, ask a brief clarifying question yourself
   instead of guessing.
3. Never fabricate information the sub-agents didn't return.
4. Pass along the sub-agent's citations/results faithfully.
""",
    sub_agents=[rag_agent, email_agent, calendar_agent],
)

# ADK CLI / `adk web` looks for a module-level `root_agent`.
root_agent = manager_agent