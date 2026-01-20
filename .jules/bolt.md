# Bolt's Journal ⚡

## CRITICAL LEARNINGS
*Only add entries for CRITICAL learnings that will help avoid mistakes or make better decisions.*

## 2024-05-22 - Starlette BaseHTTPMiddleware & Content-Length
**Learning:** `BaseHTTPMiddleware` consumes the response stream to allow modification, which converts the response to a `StreamingResponse` and strips the `Content-Length` header. This breaks downstream middleware that relies on `Content-Length` (like `GZipMiddleware` with `minimum_size`).
**Action:** Use pure ASGI middleware (implementing `__call__`) instead of `BaseHTTPMiddleware` for simple header modifications to preserve `Content-Length` and improve performance by avoiding re-streaming.
