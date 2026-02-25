"""Auth/settings configuration tests."""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from backend.api import auth
from backend.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_create_access_token_uses_env_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "unit-test-jwt-secret-32-bytes-minimum")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    token = auth.create_access_token(  # allow-secret (false positive: test token)
        {"sub": "alice"},
        expires_delta=timedelta(minutes=5),
    )

    decoded = jwt.decode(
        token,
        "unit-test-jwt-secret-32-bytes-minimum",
        algorithms=["HS256"],
    )
    assert decoded["sub"] == "alice"


def test_production_requires_explicit_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    # Force empty values so local .env file fallbacks do not mask the production requirement.
    monkeypatch.setenv("JWT_SECRET_KEY", "")
    monkeypatch.setenv("JWT_SECRET", "")
    monkeypatch.setenv("SECRET_KEY", "")

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        _ = get_settings().jwt_secret_key_resolved
