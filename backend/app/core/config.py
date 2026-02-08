# [Feature: Infrastructure] [Story: Backend Setup] [Ticket: NM-ADMIN-001-DB-T01]
"""
Application Settings

Loads configuration from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "GAIA Template"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/appdb"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5188", "http://localhost:3000"]
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
