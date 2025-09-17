from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    MONGODB_URI: str
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str
    PORT: int
    ENV: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
