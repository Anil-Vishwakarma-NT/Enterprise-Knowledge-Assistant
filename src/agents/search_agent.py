from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from src.config import OLLAMA_MODEL
from src.tools.search_tool import search_documents

search_agent = Agent(
    name="search_agent",
    model=LiteLlm(model=OLLAMA_MODEL),
    description=(
        "Answers employee questions by searching the enterprise document "
        "knowledge base (policies, handbooks, manuals, guides)."
    ),
    instruction="""
You are the Enterprise Search Agent.

### CRITICAL RULES:
1. Always execute the `search_documents` tool before answering any factual or policy question.
2. ALWAYS pass a meaningful search string as the `query` parameter when calling `search_documents`. Never call the tool with empty arguments.
3. Base your answer STRICTLY on the retrieved passages returned by `search_documents`.
4. DO NOT include source file names, document titles, or page citations in your final answer unless explicitly asked by the user.
5. Keep your responses direct, professional, and clear.
6. If no relevant information is found in the tool output, state clearly: "I could not find information regarding this in the enterprise documents."
""",
    tools=[search_documents],
)