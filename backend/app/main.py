"""
Main FastAPI application
MedAI Dermatology - Backend API for skin lesion diagnosis
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid
import base64
import cv2
import numpy as np

from .config import settings
from .models.schemas import (
    PredictionResponse,
    DiagnosisHistory,
    HistoryListResponse,
    HealthResponse,
    PreviewResponse
)
from .services.preprocessing import validate_image, preprocess_image, save_uploaded_image
from .services.inference import model_service
from .services.storage import storage_service
from .utils.constants import (
    DISEASE_NAMES_VI,
    DISEASE_NAMES_EN,
    RISK_LEVELS,
    RISK_LEVEL_VI,
    RECOMMENDATIONS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API chẩn đoán bệnh da bằng AI sử dụng EfficientNet-B3",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount uploads directory to serve images
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Configure CORS - Allow all origins for development
# NOTE: In production, replace "*" with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Model path: {settings.MODEL_PATH}")
    
    # Model is loaded in ModelInference __init__
    if model_service.is_loaded():
        logger.info("✓ AI Model loaded successfully")
    else:
        logger.error("✗ Failed to load AI model")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "MedAI Dermatology API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=model_service.is_loaded(),
        version=settings.VERSION
    )


@app.post(
    f"{settings.API_V1_PREFIX}/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Upload ảnh và nhận chẩn đoán",
    description="Upload ảnh da để AI phân tích và đưa ra chẩn đoán bệnh"
)
async def predict(file: UploadFile = File(..., description="Ảnh da cần chẩn đoán")):
    """
    Endpoint chính để upload ảnh và nhận dự đoán
    
    - **file**: File ảnh (JPG, PNG, HEIC) tối đa 10MB
    
    Returns dự đoán với confidence score và khuyến nghị y tế
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate image
        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Generate unique diagnosis ID
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        diagnosis_id = f"DIAG-{timestamp_str}-{unique_id}"
        
        # Preprocess image
        logger.info(f"Preprocessing image for diagnosis {diagnosis_id}")
        preprocessed_img = preprocess_image(file_content)
        
        # Run prediction
        logger.info(f"Running AI prediction for {diagnosis_id}")
        predicted_class, confidence, all_predictions = model_service.predict(preprocessed_img)
        
        # Get disease information
        disease_name_vi = DISEASE_NAMES_VI.get(predicted_class, "Không xác định")
        disease_name_en = DISEASE_NAMES_EN.get(predicted_class, "Unknown")
        risk_level = RISK_LEVELS.get(predicted_class, "medium")
        risk_level_vi = RISK_LEVEL_VI.get(risk_level, "Trung bình")
        recommendations = RECOMMENDATIONS.get(predicted_class, {
            "description": "Vui lòng tư vấn bác sĩ da liễu",
            "actions": ["Khám bác sĩ chuyên khoa"],
            "urgency": "Nên khám"
        })
        
        # Create response
        response = PredictionResponse(
            diagnosis_id=diagnosis_id,
            predicted_class=predicted_class,
            disease_name_vi=disease_name_vi,
            disease_name_en=disease_name_en,
            confidence=confidence,
            confidence_percent=f"{confidence * 100:.1f}%",
            risk_level=risk_level,
            risk_level_vi=risk_level_vi,
            all_predictions=all_predictions,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        # Save uploaded image
        try:
            await save_uploaded_image(file_content, diagnosis_id)
            logger.info(f"Saved image for {diagnosis_id}")
        except Exception as e:
            logger.warning(f"Failed to save image: {e}")
        
        # Save to database
        try:
            await storage_service.save_diagnosis(response)
            logger.info(f"Saved diagnosis {diagnosis_id} to database")
        except Exception as e:
            logger.warning(f"Failed to save to database: {e}")
        
        logger.info(
            f"Prediction complete: {diagnosis_id} -> {predicted_class} "
            f"({confidence:.2%})"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý ảnh: {str(e)}"
        )


@app.get(
    f"{settings.API_V1_PREFIX}/history",
    response_model=HistoryListResponse,
    tags=["History"],
    summary="Lấy lịch sử chẩn đoán",
    description="Lấy danh sách các chẩn đoán đã thực hiện"
)
async def get_history(limit: int = 100):
    """
    Lấy danh sách lịch sử chẩn đoán
    
    - **limit**: Số lượng record tối đa (mặc định 100)
    
    Returns danh sách các chẩn đoán đã thực hiện
    """
    try:
        records = await storage_service.get_all_diagnoses(limit=limit)
        
        return HistoryListResponse(
            total=len(records),
            records=records
        )
        
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy lịch sử: {str(e)}"
        )


@app.get(
    f"{settings.API_V1_PREFIX}/history/{{diagnosis_id}}",
    response_model=PredictionResponse,
    tags=["History"],
    summary="Lấy chi tiết chẩn đoán",
    description="Lấy thông tin chi tiết của một chẩn đoán theo ID"
)
async def get_diagnosis(diagnosis_id: str):
    """
    Lấy chi tiết một chẩn đoán cụ thể
    
    - **diagnosis_id**: ID của chẩn đoán
    
    Returns thông tin chi tiết chẩn đoán
    """
    try:
        diagnosis = await storage_service.get_diagnosis_by_id(diagnosis_id)
        
        if diagnosis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy chẩn đoán với ID: {diagnosis_id}"
            )
        
        return diagnosis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diagnosis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin chẩn đoán: {str(e)}"
        )



@app.post(
    f"{settings.API_V1_PREFIX}/predict/preview",
    response_model=PreviewResponse,
    tags=["Prediction"],
    summary="Xem trước tiền xử lý ảnh",
    description="Upload ảnh và nhận lại ảnh đã qua tiền xử lý (segmentation, hair removal, resize)"
)
async def preview_preprocessing(file: UploadFile = File(..., description="Ảnh da cần xem trước")):
    """
    Endpoint xem trước kết quả tiền xử lý
    
    - **file**: File ảnh (JPG, PNG, HEIC) tối đa 10MB
    
    Returns ảnh đã qua xử lý dưới dạng base64
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate image (reuse existing validation)
        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Preprocess image
        logger.info(f"Preprocessing preview for image: {file.filename}")
        
        # Process the image with steps
        preprocessed_img, steps = preprocess_image(file_content, return_steps=True)
        
        # Remove batch dimension if present (1, H, W, C) -> (H, W, C)
        if len(preprocessed_img.shape) == 4:
            preprocessed_img = np.squeeze(preprocessed_img, axis=0)
        
        # Helper to encode image
        def encode_image(img_arr):
            if img_arr.dtype == np.float32 or img_arr.dtype == np.float64:
                if img_arr.max() <= 1.05:
                     img_arr = (img_arr * 255).astype(np.uint8)
                else:
                     img_arr = img_arr.astype(np.uint8)
            else:
                img_arr = img_arr.astype(np.uint8)
            
            # Convert RGB to BGR
            img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            
            # Encode
            _, buffer = cv2.imencode('.jpg', img_bgr)
            return base64.b64encode(buffer).decode('utf-8')

        # Encode main processed image
        jpg_as_text = encode_image(preprocessed_img)
        
        # Encode steps
        encoded_steps = {}
        if steps:
            for key, img in steps.items():
                encoded_steps[key] = f"data:image/jpeg;base64,{encode_image(img)}"
        
        return PreviewResponse(
            processed_image=f"data:image/jpeg;base64,{jpg_as_text}",
            steps=encoded_steps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý ảnh preview: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
