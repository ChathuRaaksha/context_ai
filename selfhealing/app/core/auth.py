"""
API key authentication functions for securing endpoints.
Supports multiple authentication methods: Bearer token, X-API-Key header, and query parameter.
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional, Tuple
from fastapi import Header, Query, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_database

security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The API key to hash

    Returns:
        str: Hexadecimal hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_api_key() -> Tuple[str, str]:
    """
    Generate a new API key and its hash.

    Returns:
        Tuple[str, str]: (raw_api_key, hashed_api_key)
    """
    # Generate a secure random API key
    raw_key = f"aibh_{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(raw_key)

    return raw_key, hashed_key


async def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key against stored hashed keys in the database.

    Args:
        api_key: The API key to verify

    Returns:
        bool: True if the API key is valid and active, False otherwise
    """
    try:
        db = await get_database()
        key_hash = hash_api_key(api_key)

        # Find the API key in database
        api_key_doc = await db.api_keys.find_one({
            "key_hash": key_hash,
            "is_active": True
        })

        if api_key_doc:
            # Update last_used_at timestamp
            await db.api_keys.update_one(
                {"key_hash": key_hash},
                {"$set": {"last_used_at": datetime.utcnow()}}
            )
            return True

        return False

    except Exception:
        return False


async def get_api_key(
    authorization: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None)
) -> Optional[str]:
    """
    Extract API key from multiple possible sources:
    1. Bearer token in Authorization header
    2. X-API-Key header
    3. api_key query parameter

    Args:
        authorization: Bearer token from Authorization header
        x_api_key: API key from X-API-Key header
        api_key: API key from query parameter

    Returns:
        Optional[str]: The extracted API key or None

    Raises:
        HTTPException: If authentication fails
    """
    # Try Bearer token
    if authorization:
        if await verify_api_key(authorization.credentials):
            return authorization.credentials

    # Try X-API-Key header
    if x_api_key:
        if await verify_api_key(x_api_key):
            return x_api_key

    # Try query parameter
    if api_key:
        if await verify_api_key(api_key):
            return api_key

    # If we got here and any auth was provided, it was invalid
    if authorization or x_api_key or api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )

    # No auth provided - this is okay for optional auth
    return None


async def require_api_key(
    api_key: Optional[str] = Security(get_api_key)
) -> str:
    """
    Dependency that requires a valid API key.

    Args:
        api_key: API key from get_api_key dependency

    Returns:
        str: The validated API key

    Raises:
        HTTPException: If no valid API key is provided
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via Bearer token, X-API-Key header, or api_key query parameter."
        )
    return api_key


async def optional_api_key(
    api_key: Optional[str] = Security(get_api_key)
) -> Optional[str]:
    """
    Dependency that allows optional API key authentication.

    Args:
        api_key: API key from get_api_key dependency

    Returns:
        Optional[str]: The validated API key or None
    """
    return api_key
