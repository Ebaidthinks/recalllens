"""
Configuration settings for RecallLens backend
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    app_name: str = "RecallLens API"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Settings
    cors_origins: list = ["*"]  # In production, specify actual origins

    # File Storage
    base_dir: Path = Path(__file__).parent
    upload_dir: Path = base_dir / "assets" / "uploads"
    output_dir: Path = base_dir / "assets" / "outputs"
    max_upload_size_mb: int = 50

    # Model Settings
    ocr_lang: str = "en"
    ocr_use_gpu: bool = False  # Set to True if GPU available

    # Processing Settings
    default_speed_kmh: float = 100.0
    default_view_distance_m: float = 40.0
    default_dwell_sec: float = 1.0
    default_lighting: str = "day"
    default_distraction: str = "low"

    # Video Generation
    video_fps: int = 30
    video_duration_sec: int = 3

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
