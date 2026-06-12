import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic AI Hiring Copilot"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET: str = "super-secret-key-change-in-production-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/hiring_copilot"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector Store
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "resumes"
    
    # AI Configuration
    GROQ_API_KEY: str = ""
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    
    # OCR
    OCR_ENABLED: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
