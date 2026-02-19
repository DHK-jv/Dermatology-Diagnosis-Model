"""
Pydantic schemas for request/response models
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint"""
    diagnosis_id: str = Field(..., description="Unique identifier for this diagnosis")
    predicted_class: str = Field(..., description="Predicted disease class code")
    disease_name_vi: str = Field(..., description="Disease name in Vietnamese")
    disease_name_en: str = Field(..., description="Disease name in English")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    confidence_percent: Optional[str] = Field(None, description="Confidence as percentage string")
    risk_level: str = Field(..., description="Risk level: low/medium/high/very_high")
    risk_level_vi: str = Field(..., description="Risk level in Vietnamese")
    all_predictions: Dict[str, float] = Field(..., description="All class probabilities")
    recommendations: Dict = Field(..., description="Medical recommendations")
    timestamp: datetime = Field(default_factory=datetime.now, description="Prediction timestamp")
    
    def __init__(self, **data):
        """Initialize and auto-calculate confidence_percent if missing"""
        # Auto-calculate confidence_percent from confidence if not provided
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
                "timestamp": "2026-01-27T03:30:00"
            }
        }


class DiagnosisHistory(BaseModel):
    """Model for a single diagnosis history record"""
    diagnosis_id: str
    predicted_class: str
    disease_name_vi: str
    confidence: float
    risk_level: str
    risk_level_vi: str
    timestamp: datetime
    image_filename: Optional[str] = None
    
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
                "image_filename": "upload_001.jpg"
            }
        }


class HistoryListResponse(BaseModel):
    """Response model for history list endpoint"""
    total: int = Field(..., description="Total number of records")
    records: List[DiagnosisHistory] = Field(..., description="List of diagnosis records")
    
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
                        "timestamp": "2026-01-27T03:30:00"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy", description="Service status")
    model_loaded: bool = Field(..., description="Whether AI model is loaded")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)


class PreviewResponse(BaseModel):
    """Response model for preprocessing preview endpoint"""
    processed_image: str = Field(..., description="Base64 encoded processed image")
    steps: Optional[Dict[str, str]] = Field(None, description="Base64 encoded intermediate steps")
    
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
    """Response model for GradCAM explainability endpoint"""
    heatmap_overlay: str = Field(..., description="Base64 encoded heatmap overlay image")
    predicted_class: str = Field(..., description="The class GradCAM was generated for")
    class_idx: int = Field(..., description="Class index used for GradCAM")
    
    class Config:
        json_schema_extra = {
            "example": {
                "heatmap_overlay": "data:image/jpeg;base64,...",
                "predicted_class": "melanoma",
                "class_idx": 14
            }
        }
