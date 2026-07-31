from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.config import OLLAMA_MODEL
from src.tools.search_tool import search_documents

search_agent = Agent(
    name="search_agent",
    model=LiteLlm(model=OLLAMA_MODEL),
    description=(
        "Answers employee questions by searching the enterprise document "
        "knowledge base (policies, handbooks, manuals, guides) and returning "
        "citation-backed answers."
    ),
    instruction="""
You are the Enterprise Search Agent.

- Always call the `search_documents` tool before answering a knowledge question.
- Base your answer ONLY on the retrieved passages. If nothing relevant was
  found, say so honestly instead of guessing.
- Every factual claim must be followed by a citation in the form
  (Source: <source>, page <page>).
- Keep answers concise and business-appropriate.
""",
    tools=[search_documents],
)
