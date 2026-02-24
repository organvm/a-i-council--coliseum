import os
import pytest
from unittest.mock import patch

# Ensure we use an in-memory SQLite database for tests to prevent connection errors.
# Must be set before importing any backend modules that load database.py
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///.test.db"

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup environment variables and mock background workers for tests."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""}), \
         patch("backend.event_pipeline.worker.AutonomousArenaWorker.start"), \
         patch("backend.social.twitch_listener.TwitchListener.start"), \
         patch("backend.ai_agents.orchestrator.SystemOrchestrator.load_state"), \
         patch("backend.ai_agents.orchestrator.SystemOrchestrator._persist_vote_to_db"):
        yield


