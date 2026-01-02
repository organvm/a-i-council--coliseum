## 2024-05-23 - [Input Sanitization Gap in Event Ingestion]
**Vulnerability:** The `EventIngestionSystem` blindly copied raw input fields (`title`, `description`, `content`) into the `NormalizedEvent` model. While `EventSource.USER_SUBMISSION` is not yet fully exposed, the underlying method `_default_normalize` was a latent XSS vector.
**Learning:** Even placeholder or "internal" systems often get wired up to public inputs faster than security reviews happen. Pydantic models validate types but do not sanitize content by default.
**Prevention:** Explicitly use `html.escape()` (or `bleach` for rich text) at the boundary where raw data enters the system. Added `html.escape()` to `backend/event_pipeline/ingestion.py`. Also deprecated `datetime.utcnow()` usage in favor of timezone-aware UTC.
