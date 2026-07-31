"""
Centralized configuration for the Enterprise Knowledge Assistant (EKA).
Loads everything from environment variables / .env so no secrets or
hardcoded paths live inside the agent/tool code.
"""
import os
from dotenv import load_dotenv

from pathlib import Path 

load_dotenv() # <--- Make sure this line is present at the top!

# Project base directory definition
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory definitions
DATA_DIR = BASE_DIR / "data"
INGESTION_MANIFEST_PATH = DATA_DIR / "ingestion_manifest.json"

# ---- Ollama (terminal only, no desktop app required) ----
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama_chat/llama3.1")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ADK's LiteLLM connector reads OLLAMA_API_BASE from the environment for
# the ollama_chat/* provider, so we make sure it's exported for the process.
os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_API_BASE)

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", os.path.join(BASE_DIR, "vectorstore"))

CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "enterprise_docs")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

TOP_K_DEFAULT = int(os.getenv("TOP_K_DEFAULT", "4"))

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

EMAIL_DRAFTS_PATH = os.getenv("EMAIL_DRAFTS_PATH", "./data/email_drafts.json")

# ---- Gmail + Calendar (OAuth) ----
# Use BASE_DIR to build absolute paths so execution location doesn't matter
GMAIL_CREDENTIALS_PATH = os.getenv(
    "GMAIL_CREDENTIALS_PATH", 
    str(BASE_DIR / "credentials.json")
)

GMAIL_TOKEN_PATH = os.getenv(
    "GMAIL_TOKEN_PATH", 
    str(BASE_DIR / "token.json")
)

GMAIL_SENDER_LABEL = os.getenv("GMAIL_SENDER_LABEL", "me")