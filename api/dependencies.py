"""
FastAPI Dependencies

Authentication, database, and other injectors for the Query layer.
"""

import os
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel


# Security scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT token payload."""
    user_id: int
    tenant_id: Optional[int] = None
    exp: int


class CurrentUser(BaseModel):
    """Current authenticated user from token."""
    id: int
    tenant_id: Optional[int] = None


def get_secret_key() -> str:
    """Get the JWT secret key from settings."""
    return os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-me')


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    Validate JWT token and return current user.
    
    This is a simplified version - in production, you might want to
    fetch the full user from the database.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            get_secret_key(),
            algorithms=["HS256"]
        )
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return CurrentUser(
            id=user_id,
            tenant_id=payload.get("tenant_id")
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Optionally get current user - doesn't fail if not authenticated.
    Useful for public endpoints that show extra data for logged-in users.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def get_db_connection():
    """
    Get a database connection for raw SQL queries.
    
    For optimized queries that bypass Django ORM.
    """
    from django.db import connection
    return connection
