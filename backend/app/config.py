"""
Cấu hình cài đặt cho ứng dụng
"""
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Đọc biến môi trường từ file .env (Tìm ở thư mục gốc dự án)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if not env_path.exists():
    # Trường hợp chạy trong Docker (hf_deployment_ready)
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class Settings:
    """Cài đặt ứng dụng"""
    
    # Đường dẫn
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    DEFAULT_MODEL_PATH: Path = BASE_DIR / "ml_models" / "efficientnet_b4_derma_v3_0.pth"  # Model V3.0 (độ chính xác tập val ~88.0%)
    MODEL_PATH: Path = DEFAULT_MODEL_PATH
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
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "medai_dermatology")
    
    # Cài đặt lưu trữ
    USE_MONGODB: bool = os.getenv("USE_MONGODB", "false").lower() == "true"
    HISTORY_FILE: Path = BASE_DIR / "history.json"
    
    # Cài đặt hình ảnh
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "heic"}
    IMAGE_SIZE: tuple = (380, 380)  # Kích thước đầu vào mô hình
    
    # Cài đặt mô hình
    CONFIDENCE_THRESHOLD: float = 0.5
    MODEL_REQUIRED: bool = os.getenv("MODEL_REQUIRED", "false").lower() == "true"
    
    # Preprocessing & Hardware optimization
    PREPROCESSING_MODE: str = os.getenv("PREPROCESSING_MODE", "auto")
    TORCH_THREADS: int = int(os.getenv("TORCH_THREADS", "1"))
    
    def __init__(self):
        """Khởi tạo cài đặt và tạo các thư mục cần thiết"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Cho phép override đường dẫn model qua env (phù hợp production/Render)
        env_model_path = os.getenv("MODEL_PATH")
        if env_model_path:
            self.MODEL_PATH = Path(env_model_path)
        else:
            self.MODEL_PATH = self.DEFAULT_MODEL_PATH

        # Fallback cho môi trường dev nếu model được đặt ở thư mục research/kaggle_result/
        if not self.MODEL_PATH.exists():
            fallback_path = (
                self.PROJECT_ROOT
                / "research"
                / "kaggle_result"
                / "kaggle_train_v3.0_results"
                / "efficientnet_b4_derma_v3_0.pth"
            )
            if fallback_path.exists():
                self.MODEL_PATH = fallback_path

        # Logging kiểm tra MongoDB (chỉ log trạng thái, không log chuỗi kết nối nhạy cảm)
        if self.USE_MONGODB:
            if not self.MONGODB_URL:
                logger.error("❌ USE_MONGODB=true but MONGODB_URL is missing!")
            else:
                logger.info(f"✓ MongoDB configuration detected (Database: {self.MONGODB_DB_NAME})")

        # Kiểm tra sự tồn tại của mô hình
        if not self.MODEL_PATH.exists():
            message = (
                f"Model not found at {self.MODEL_PATH}. "
                "Set MODEL_PATH env var to the weights file location."
            )
            if self.MODEL_REQUIRED:
                raise FileNotFoundError(message)
            logger.warning(message)

# Tạo một instance cài đặt toàn cục
settings = Settings()
