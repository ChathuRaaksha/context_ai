"""
Pydantic models for API key management.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APIKey(BaseModel):
    """
    API Key model for authentication.

    Attributes:
        key_hash: SHA-256 hash of the API key
        key_name: Human-readable name for the key
        description: Optional description of the key's purpose
        created_at: Timestamp when the key was created
        last_used_at: Timestamp when the key was last used
        is_active: Whether the key is currently active
    """

    key_hash: str = Field(..., description="SHA-256 hash of the API key")
    key_name: str = Field(..., description="Human-readable name for the key")
    description: Optional[str] = Field(None, description="Description of the key's purpose")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(default=True, description="Whether the key is active")

    class Config:
        json_schema_extra = {
            "example": {
                "key_hash": "a1b2c3d4e5f6...",
                "key_name": "Production API Key",
                "description": "API key for production monitoring",
                "created_at": "2025-01-15T10:30:00Z",
                "last_used_at": "2025-01-15T12:45:00Z",
                "is_active": True
            }
        }


class APIKeyCreate(BaseModel):
    """
    Request model for creating a new API key.

    Attributes:
        key_name: Human-readable name for the key
        description: Optional description of the key's purpose
    """

    key_name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Description of the key's purpose")

    class Config:
        json_schema_extra = {
            "example": {
                "key_name": "Production API Key",
                "description": "API key for production monitoring"
            }
        }


class APIKeyResponse(BaseModel):
    """
    Response model when creating a new API key.
    Contains the raw key which is shown only once.

    Attributes:
        api_key: The raw API key (shown only once)
        key_name: Human-readable name for the key
        created_at: Timestamp when the key was created
        message: Instructions for the user
    """

    api_key: str = Field(..., description="The raw API key - store this securely")
    key_name: str = Field(..., description="Name of the API key")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(
        default="Store this API key securely. It will not be shown again.",
        description="Important message for the user"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "aibh_abc123xyz789...",
                "key_name": "Production API Key",
                "created_at": "2025-01-15T10:30:00Z",
                "message": "Store this API key securely. It will not be shown again."
            }
        }


class APIKeyInfo(BaseModel):
    """
    Public information about an API key (without the actual key).

    Attributes:
        key_name: Human-readable name for the key
        description: Optional description of the key's purpose
        created_at: Timestamp when the key was created
        last_used_at: Timestamp when the key was last used
        is_active: Whether the key is currently active
    """

    key_name: str
    description: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "key_name": "Production API Key",
                "description": "API key for production monitoring",
                "created_at": "2025-01-15T10:30:00Z",
                "last_used_at": "2025-01-15T12:45:00Z",
                "is_active": True
            }
        }
