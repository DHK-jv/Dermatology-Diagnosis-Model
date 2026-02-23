"""
Cấu hình cài đặt cho ứng dụng
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Đọc biến môi trường từ file .env
load_dotenv()

class Settings:
    """Cài đặt ứng dụng"""
    
    # Đường dẫn
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    MODEL_PATH: Path = BASE_DIR / "ml_models" / "efficientnet_b4_derma_v2_1_finetuned.pth"  # Model V2.1 (độ chính xác tập val 86.2%)
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    # Cài đặt API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MedAI Dermatology API"
    VERSION: str = "1.0.0"
    
    # Cài đặt CORS
    CORS_ORIGINS: list = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ]
    
    # Cài đặt MongoDB (tùy chọn - dự phòng bằng JSON nếu không có)
    MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL", None)
    MONGODB_DB_NAME: str = "medai_dermatology"
    
    # Cài đặt lưu trữ
    USE_MONGODB: bool = os.getenv("USE_MONGODB", "false").lower() == "true"
    HISTORY_FILE: Path = BASE_DIR / "history.json"
    
    # Cài đặt hình ảnh
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "heic"}
    IMAGE_SIZE: tuple = (380, 380)  # Kích thước đầu vào mô hình
    
    # Cài đặt mô hình
    CONFIDENCE_THRESHOLD: float = 0.5
    
    def __init__(self):
        """Khởi tạo cài đặt và tạo các thư mục cần thiết"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Kiểm tra sự tồn tại của mô hình
        if not self.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {self.MODEL_PATH}. "
                f"Please ensure the model file is in the correct location."
            )

# Tạo một instance cài đặt toàn cục
settings = Settings()
