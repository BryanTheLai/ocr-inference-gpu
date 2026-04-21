# src/config.py
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from a .env file
load_dotenv()

class Settings(BaseModel):
    """Defines application-wide settings."""
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create a single, importable instance of the settings
settings = Settings()

print("✅ Configuration loaded.")
print(f"   - Redis URL: {settings.REDIS_URL}")