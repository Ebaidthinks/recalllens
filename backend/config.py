"""
Configuration settings for RecallLens backend
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# File upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# Processing parameters
SPEED_MIN = 60
SPEED_MAX = 140
DISTANCE_MIN = 20
DISTANCE_MAX = 60
DWELL_MIN = 0.5
DWELL_MAX = 2.0

LIGHTING_OPTIONS = ["day", "dusk", "night"]
DISTRACTION_OPTIONS = ["low", "med", "high"]

# API settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
