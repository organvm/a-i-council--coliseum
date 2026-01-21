## 2024-05-22 - [CRITICAL] Corrupted Agent Implementation
**Vulnerability:** Found `backend/ai_agents/agent.py` was corrupted with duplicated class definitions and syntax errors, likely due to a bad merge. This could lead to undefined behavior or service failure.
**Learning:** Core files can be silently broken if not covered by CI/CD or if merge conflicts are resolved poorly.
**Prevention:** Add pre-commit hooks that run syntax checks (`python -m py_compile`) on all files.

## 2024-05-22 - [HIGH] Missing Input Validation for Agent Creation
**Vulnerability:** `CreateAgentRequest` accepted arbitrary strings for `name`, allowing potential DoS (huge strings) or logical errors (empty names).
**Learning:** API models often default to basic types. Explicit validation using `Field` is necessary for security.
**Prevention:** Enforce Pydantic `Field` usage with `min_length`, `max_length`, and `pattern` for all string inputs in API models.
