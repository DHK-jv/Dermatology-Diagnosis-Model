"""
Configuration settings for the application
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings"""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    MODEL_PATH: Path = BASE_DIR / "ml_models" / "efficientnet_b4_derma_v2.pth"  # V2 model (73.9% val acc)
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MedAI Dermatology API"
    VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ]
    
    # MongoDB Settings (optional - fallback to JSON if not available)
    MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL", None)
    MONGODB_DB_NAME: str = "medai_dermatology"
    
    # Storage Settings
    USE_MONGODB: bool = os.getenv("USE_MONGODB", "false").lower() == "true"
    HISTORY_FILE: Path = BASE_DIR / "history.json"
    
    # Image Settings
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "heic"}
    IMAGE_SIZE: tuple = (380, 380)  # Model input size
    
    # Model Settings
    CONFIDENCE_THRESHOLD: float = 0.5
    
    def __init__(self):
        """Initialize settings and create necessary directories"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Verify model exists
        if not self.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {self.MODEL_PATH}. "
                f"Please ensure the model file is in the correct location."
            )

# Create global settings instance
settings = Settings()
