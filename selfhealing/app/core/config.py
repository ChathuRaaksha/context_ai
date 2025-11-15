"""
Configuration settings for the AI-Powered Bug Detection & Self-Healing System.
Uses Pydantic settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        MONGODB_URI: MongoDB connection string
        OPENROUTER_API_KEY: API key for OpenRouter service
        OPENROUTER_BASE_URL: Base URL for OpenRouter API
        PORT: Application port number
        ENV: Environment (development, staging, production)
        GITHUB_TOKEN: Optional GitHub token for issue creation
        GITHUB_REPO: Optional GitHub repository for issue creation
    """

    MONGODB_URI: str = "mongodb://localhost:27017"
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    PORT: int = 8000
    ENV: str = "development"

    # Optional GitHub integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI-Powered Bug Detection & Self-Healing System"

    # AI Model Configuration
    AI_MODEL: str = "anthropic/claude-3.5-sonnet"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 4000

    # Self-Healing Configuration
    AUTO_HEAL_LOW_RISK: bool = True
    AUTO_HEAL_MEDIUM_RISK: bool = True
    AUTO_HEAL_HIGH_RISK: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a singleton instance
settings = Settings()
