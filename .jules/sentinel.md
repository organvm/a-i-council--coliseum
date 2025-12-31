## 2024-05-23 - Unvalidated Input in Event Ingestion
**Vulnerability:** The `EventIngestionSystem` was blindly copying raw input data into `NormalizedEvent` objects without any sanitization. This allowed `USER_SUBMISSION` sources (and others) to inject arbitrary HTML, including `<script>` tags, leading to Stored XSS.
**Learning:** The system relies on Pydantic models for structure but lacked validation/sanitization logic. Type hints (`str`) are not security boundaries.
**Prevention:** I implemented a `field_validator` on the `NormalizedEvent` model to automatically sanitize HTML content in `title`, `description`, and `content` fields using `html.escape`. This ensures that even if a data source is compromised or malicious, the backend neutralizes the payload before storage.
