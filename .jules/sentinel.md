## 2026-01-17 - API Input Validation & Corrupted Codebase
**Vulnerability:** API endpoints in `blockchain.py` and `voting.py` lacked Pydantic validation (e.g., negative amounts allowed).
**Learning:** Discovered `backend/ai_agents/agent.py` contained duplicate code blocks (merge conflict artifact), causing syntax errors and blocking tests. This highlights the importance of checking codebase health before applying security patches.
**Prevention:** Enforce strict Pydantic `Field` validation on all API models. Ensure CI runs unit tests to catch corrupted files.
