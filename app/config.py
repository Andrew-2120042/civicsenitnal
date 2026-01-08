"""Application configuration using Pydantic Settings."""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./civicsentinel.db"

    # YOLO Model Configuration
    model_path: str = "models/yolov8s.pt"
    model_confidence_threshold: float = 0.5
    model_frame_size: int = 640

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # User Limits
    max_cameras_free_plan: int = 10  # Increased for development
    max_cameras_pro_plan: int = 10

    # Performance
    max_workers: int = 4
    batch_size: int = 4

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Test API Key (for development)
    test_api_key: str = "test_api_key_123"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
