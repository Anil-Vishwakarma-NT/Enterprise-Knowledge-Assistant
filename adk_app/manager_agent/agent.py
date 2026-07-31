import os
import sys

# Make the project root importable regardless of where `adk web`/`adk run` is launched from.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agents.manager_agent import root_agent