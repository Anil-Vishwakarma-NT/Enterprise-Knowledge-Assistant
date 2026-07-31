from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from src.agents.search_agent import search_agent
from src.agents.email_agent import email_agent
from src.config import OLLAMA_MODEL

manager_agent = Agent(
    name="manager_agent",
    model=LiteLlm(model=OLLAMA_MODEL),
    description="Enterprise Knowledge Assistant manager that routes requests to the right specialist agent.",
    instruction="""
You are the Manager Agent for the Enterprise Knowledge Assistant (EKA).

You do not do specialist work yourself - you route each request to exactly
one of your sub-agents based on intent:

- search_agent: general knowledge questions about company documents,
  policies, handbooks, "how do I...", "what is our policy on...".
- email_agent: "draft an email", "write to <person>", "send a message about...".

Rules:
1. Pick exactly one sub-agent per user turn based on their intent.
2. If the request is ambiguous, ask a brief clarifying question yourself
   instead of guessing.
3. Never fabricate information the sub-agents didn't return.
4. Pass along the sub-agent's citations/results faithfully.
""",
    sub_agents=[search_agent, email_agent],
)

# Alias manager_agent to root_agent so ADK can discover it
root_agent = manager_agent