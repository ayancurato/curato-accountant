import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    GROQ_API_KEY: str = "mock-api-key"
    GROQ_MODEL: str = "qwen/qwen-3.8-27b"
    MAX_UPLOAD_SIZE_MB: int = 10
    STORAGE_PATH: str = "./storage/documents"
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Ensure storage path exists
Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
