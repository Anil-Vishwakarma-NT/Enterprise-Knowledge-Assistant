"""
Centralized configuration for the Enterprise Knowledge Assistant (EKA).
Loads everything from environment variables / .env so no secrets or
hardcoded paths live inside the agent/tool code.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Ollama (terminal only, no desktop app required) ----
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama_chat/llama3.1")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ADK's LiteLLM connector reads OLLAMA_API_BASE from the environment for
# the ollama_chat/* provider, so we make sure it's exported for the process.
os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_API_BASE)