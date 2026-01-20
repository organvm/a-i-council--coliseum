## 2026-01-20 - [Input Validation for Critical APIs]
**Vulnerability:** API endpoints for financial (`/stake`, `/transfer`) and voting (`/create_session`) operations lacked input validation, allowing negative amounts and DoS via large payloads.
**Learning:** Pydantic models default to allowing any valid type (e.g. `float` accepts negative infinity), requiring explicit `Field` constraints (`gt=0`, `min_length`, etc.) to be secure by default.
**Prevention:** Always use `pydantic.Field` with `gt`, `ge`, `min_length`, `max_length` constraints for all external input models, especially for financial or resource-intensive fields.
