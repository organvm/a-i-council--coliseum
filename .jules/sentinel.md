# Sentinel Security Journal
## 2025-02-18 - Middleware Ordering & Rate Limiting
**Vulnerability:** Rate limiting returning 429 responses without CORS headers, causing "Network Error" in browsers instead of readable status codes.
**Learning:** In FastAPI/Starlette, middleware added via `app.add_middleware` runs in reverse order of addition for requests (LIFO). To ensure CORS headers are applied even to 429s from rate limiting, `CORSMiddleware` must be the outermost layer, meaning it must be added *last*.
**Prevention:** Always verify middleware order when adding security controls. Security middleware (like rate limits) should be inner to CORS but outer to application logic.

## 2025-02-18 - Duplicate Class Definitions
**Vulnerability:** `agent.py` contained two conflicting definitions of the `Agent` class. Python silently executes both, leaving the last one active, which masked the fact that the first one was incomplete.
**Learning:** Copy-paste errors can lead to "shadow code" where the visible/top code is ignored.
**Prevention:** Use linters (flake8/pylint) to catch redefinition of names.
