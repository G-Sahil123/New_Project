# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MySQL Database
    DATABASE_HOST: Optional[str] = None
    DATABASE_PORT: Optional[int] = None 
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None 
    
    # Security
    SECRET_KEY: Optional[str] = None 
    ALGORITHM: str = "HS256"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 