"""
Pydantic schemas cho mô hình request/response (đầu vào/đầu ra)
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Mô hình cơ bản cho người dùng"""
    username: str = Field(..., description="Tên đăng nhập duy nhất")
    full_name: Optional[str] = Field(None, description="Họ và tên người dùng")
    role: str = Field(default="user", description="Quyền người dùng: user, doctor, admin")


class UserCreate(UserBase):
    """Lược đồ đăng ký người dùng"""
    password: str = Field(..., description="Mật khẩu người dùng")


class UserResponse(UserBase):
    """Lược đồ trả về thông tin người dùng"""
    id: str = Field(..., description="ID người dùng")
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")


class Token(BaseModel):
    """Lược đồ trả về JWT token"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserBase] = None


class TokenData(BaseModel):
    """Lược đồ dữ liệu token payload"""
    username: Optional[str] = None
    role: Optional[str] = None


class PredictionResponse(BaseModel):
    """Mô hình phản hồi API chẩn đoán"""
    diagnosis_id: str = Field(..., description="Định danh duy nhất cho chẩn đoán này")
    predicted_class: str = Field(..., description="Mã loại bệnh dự đoán")
    disease_name_vi: str = Field(..., description="Tên bệnh bằng tiếng Việt")
    disease_name_en: str = Field(..., description="Tên bệnh bằng tiếng Anh")
    confidence: float = Field(..., ge=0, le=1, description="Độ tin cậy (0-1)")
    confidence_percent: Optional[str] = Field(None, description="Độ tin cậy theo phần trăm")
    risk_level: str = Field(..., description="Mức độ rủi ro: low/medium/high/very_high")
    risk_level_vi: str = Field(..., description="Mức độ rủi ro bằng tiếng Việt")
    all_predictions: Dict[str, float] = Field(..., description="Tất cả xác suất dự đoán của các loại bệnh")
    recommendations: Dict = Field(..., description="Khuyến nghị y tế")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian dự đoán")
    has_feedback: bool = Field(default=False, description="Cờ xác nhận kết quả này đã từng nhận được phản hồi hay chưa")
    
    def __init__(self, **data):
        """Khởi tạo và tự động tính toán confidence_percent nếu thiếu"""
        # Tự động chuyển đổi confidence sang % nếu không được truyền vào
        if 'confidence_percent' not in data and 'confidence' in data:
            data['confidence_percent'] = f"{data['confidence'] * 100:.1f}%"
        super().__init__(**data)
    
    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis_id": "DIAG-20260127-001",
                "predicted_class": "nv",
                "disease_name_vi": "Nốt ruồi lành tính",
                "disease_name_en": "Melanocytic Nevus",
                "confidence": 0.984,
                "confidence_percent": "98.4%",
                "risk_level": "low",
                "risk_level_vi": "Thấp",
                "all_predictions": {
                    "nv": 0.984,
                    "bkl": 0.012,
                    "mel": 0.003
                },
                "recommendations": {
                    "description": "Nốt ruồi lành tính...",
                    "actions": ["Theo dõi thường xuyên..."],
                    "urgency": "Không cấp thiết"
                },
                "timestamp": "2026-01-27T03:30:00",
                "has_feedback": False
            }
        }


class DiagnosisHistory(BaseModel):
    """Mô hình cho 1 bản ghi lịch sử chẩn đoán"""
    diagnosis_id: str
    predicted_class: str
    disease_name_vi: str
    confidence: float
    risk_level: str
    risk_level_vi: str
    timestamp: datetime
    image_filename: Optional[str] = None
    has_feedback: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis_id": "DIAG-20260127-001",
                "predicted_class": "nv",
                "disease_name_vi": "Nốt ruồi lành tính",
                "confidence": 0.984,
                "risk_level": "low",
                "risk_level_vi": "Thấp",
                "timestamp": "2026-01-27T03:30:00",
                "image_filename": "upload_001.jpg",
                "has_feedback": False
            }
        }


class HistoryListResponse(BaseModel):
    """Mô hình trả về danh sách lịch sử"""
    total: int = Field(..., description="Tổng số bản ghi")
    records: List[DiagnosisHistory] = Field(..., description="Danh sách các bản ghi chẩn đoán")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "records": [
                    {
                        "diagnosis_id": "DIAG-20260127-001",
                        "predicted_class": "nv",
                        "disease_name_vi": "Nốt ruồi lành tính",
                        "confidence": 0.984,
                        "risk_level": "low",
                        "risk_level_vi": "Thấp",
                        "timestamp": "2026-01-27T03:30:00",
                        "has_feedback": True
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Kiểm tra trạng thái hệ thống"""
    status: str = Field(default="healthy", description="Trạng thái dịch vụ")
    model_loaded: bool = Field(..., description="Mô hình AI đã được tải hay chưa")
    version: str = Field(..., description="Phiên bản API")
    timestamp: datetime = Field(default_factory=datetime.now)


class PreviewResponse(BaseModel):
    """Mô hình trả về cho API xem trước tiền xử lý ảnh"""
    processed_image: str = Field(..., description="Ảnh đã xử lý (Base64)")
    steps: Optional[Dict[str, str]] = Field(None, description="Các bước trung gian (Base64)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "processed_image": "data:image/jpeg;base64,...",
                "steps": {
                    "original": "data:image/jpeg;base64,...",
                    "cropped": "data:image/jpeg;base64,...",
                    "hair_removed": "data:image/jpeg;base64,..."
                }
            }
        }


class GradCAMResponse(BaseModel):
    """Mô hình trả về cho API giải thích GradCAM"""
    heatmap_overlay: str = Field(..., description="Ảnh gốc đè bằng heatmap (Base64)")
    predicted_class: str = Field(..., description="Loại bệnh được dùng để chạy heatmap")
    class_idx: int = Field(..., description="Chỉ số phân loại class (Index) của GradCAM")
    
    class Config:
        json_schema_extra = {
            "example": {
                "heatmap_overlay": "data:image/jpeg;base64,...",
                "predicted_class": "melanoma",
                "class_idx": 14
            }
        }


class FeedbackRequest(BaseModel):
    """Mô hình yêu cầu gửi đánh giá chẩn đoán AI"""
    diagnosis_id: str = Field(..., description="ID của chẩn đoán được đánh giá")
    is_correct: bool = Field(..., description="Khẳng định AI dự đoán đúng hay sai")
    actual_class: Optional[str] = Field(None, description="Loại bệnh thực tế (nếu AI sai)")
    notes: Optional[str] = Field(None, description="Ghi chú thêm từ bác sĩ/người dùng")
    
    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis_id": "DIAG-20260127-001",
                "is_correct": False,
                "actual_class": "melanoma",
                "notes": "Lesion has irregular borders not captured well."
            }
        }
