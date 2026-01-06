## 2024-05-23 - [Input Sanitization Gap in Event Ingestion]
**Vulnerability:** The `NormalizedEvent` model sanitized `title`, `description`, and `content` fields to prevent XSS, but missed `category` (Optional[str]) and `tags` (List[str]).
**Learning:** Adding new fields to a Pydantic model requires explicit updates to validators if those fields handle untrusted input. `Optional` and `List` types need careful handling in validators.
**Prevention:** When adding new fields to models that ingest external data, always audit them against existing sanitization validators. Use a generic "sanitize all string fields" approach if possible, or strictly enforce a whitelist of safe fields.
