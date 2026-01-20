import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_gzip_compression_enabled():
    """
    Verify that GZip compression is enabled for large responses.
    """
    # Create a large response endpoint dynamically
    @app.get("/test-gzip-large-response")
    def large_response():
        return {"data": "x" * 5000}  # 5000 bytes of 'x', highly compressible

    try:
        # Request with Accept-Encoding: gzip (TestClient sends this by default usually, but we can be explicit)
        response = client.get("/test-gzip-large-response", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200

        # Check Content-Encoding header
        content_encoding = response.headers.get("content-encoding", "")
        assert "gzip" in content_encoding, f"Expected 'gzip' in Content-Encoding, got '{content_encoding}'"

        # Verify Security Headers are also present (checking middleware chain)
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        # Check that the body size is significantly reduced
        # "x" * 5000 is ~5KB. Gzipped it should be very small (~30 bytes + overhead).
        content_length = int(response.headers["content-length"])
        assert content_length < 1000, f"Expected compressed size < 1000 bytes, got {content_length}"

    finally:
        # Clean up: remove the route we added
        # FastAPI stores routes in app.router.routes
        # We search for the one we added and remove it to avoid side effects
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/test-gzip-large-response"]

def test_gzip_ignored_for_small_response():
    """
    Verify that GZip compression is NOT applied for small responses (< 1000 bytes).
    """
    @app.get("/test-gzip-small-response")
    def small_response():
        return {"data": "small"}

    try:
        response = client.get("/test-gzip-small-response", headers={"Accept-Encoding": "gzip"})

        assert response.status_code == 200

        # Should NOT have Content-Encoding: gzip
        content_encoding = response.headers.get("content-encoding", "")
        assert "gzip" not in content_encoding, f"Did not expect 'gzip' for small response, got '{content_encoding}'"

    finally:
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/test-gzip-small-response"]
