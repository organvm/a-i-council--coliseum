"""
Authentication Module.

Handles JWT token generation and user validation.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login", auto_error=False)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def _auth_settings():
    return get_settings()


# Backward-compatible export used by backend.api.users.
ACCESS_TOKEN_EXPIRE_MINUTES = _auth_settings().jwt_access_token_expire_minutes


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    settings = _auth_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key_resolved,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),  # allow-secret
    db: AsyncSession = Depends(get_db)
) -> User:
    settings = _auth_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key_resolved,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),  # allow-secret
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return authenticated user when a bearer token is provided; otherwise None."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)  # allow-secret
    except HTTPException:
        return None
