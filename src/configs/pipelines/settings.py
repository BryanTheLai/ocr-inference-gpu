"""Application settings loaded from environment variables."""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Application-wide configuration values."""

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")


settings = Settings()

print("✅ Configuration loaded.")
print(f"   - Redis URL: {settings.REDIS_URL}")
