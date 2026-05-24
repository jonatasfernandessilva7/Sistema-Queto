"""
Application settings and configuration.
Centralized configuration management for the entire application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    SRC_ROOT = PROJECT_ROOT / "src"
    DATA_ROOT = PROJECT_ROOT / "data"
    
    # Data directories
    UPLOADS_DIR = DATA_ROOT / "uploads"
    AUDIOS_DIR = DATA_ROOT / "audios"
    REPORTS_DIR = DATA_ROOT / "reports"
    TEMP_DIR = DATA_ROOT / "temp"
    
    # Database
    _db_name = os.getenv("DATABASE_NAME", "memoria.db")
    # Handle SQLite URL format (e.g., "sqlite:///./queto.db" -> "queto.db")
    if _db_name.startswith("sqlite:"):
        _db_name = _db_name.split("/")[-1]
    DATABASE_NAME = _db_name if _db_name else "memoria.db"
    DATABASE_PATH = PROJECT_ROOT / DATABASE_NAME
    
    # API
    API_TITLE = "Queto System - Sistema de IA para Gerenciamento de Crises"
    API_VERSION = "1.0.0"
    API_PREFIX = "/v1"
    
    # CORS
    CORS_ORIGINS = ["*"]
    CORS_CREDENTIALS = True
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    # LLM/AI
    GROQ_API_KEY = os.getenv("API_KEY")
    GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    # Email
    ORIGIN_EMAIL = os.getenv("ORIGIN_EMAIL")
    PASSWORD_EMAIL = os.getenv("PASSWORD_EMAIL")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def ensure_directories_exist(cls) -> None:
        """Ensure all required directories exist."""
        for dir_path in [cls.UPLOADS_DIR, cls.AUDIOS_DIR, cls.REPORTS_DIR, cls.TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings instance with all configuration
    """
    # Ensure directories exist on startup
    Settings.ensure_directories_exist()
    return Settings()
