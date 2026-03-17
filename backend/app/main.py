"""
Ứng dụng FastAPI chính
MedAI Dermatology - Backend API chẩn đoán tổn thương da
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
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
    PreviewResponse,
    GradCAMResponse,
    FeedbackRequest
)
from .services.gradcam import generate_gradcam_overlay
from .services.preprocessing import validate_image, preprocess_image, save_uploaded_image
from .services.inference import model_service
from .services.storage import storage_service
from .utils.constants import (
    DISEASE_NAMES_VI,
    DISEASE_NAMES_EN,
    RISK_LEVELS,
    RISK_LEVEL_VI,
    RECOMMENDATIONS,
    MEDICAL_LOGO
)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API chẩn đoán bệnh da bằng AI sử dụng EfficientNet-B4",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Gắn thư mục uploads để phục vụ ảnh tĩnh
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Cấu hình CORS - Cho phép tất cả các nguồn trong quá trình phát triển
# LƯU Ý: Trong môi trường production, hãy thay thế "*" bằng danh sách cụ thể
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn
    allow_credentials=False,  # Phải là False khi allow_origins là "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from .services.security import SECRET_KEY, ALGORITHM, verify_password, get_password_hash, create_access_token
from .models.schemas import UserCreate, UserResponse, UserBase, Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await storage_service.get_user_by_username(username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            logger.warning("Token provided but no username in payload")
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        
        user = await storage_service.get_user_by_username(username=username)
        if user is None:
            logger.warning(f"User {username} from token not found in database")
            raise HTTPException(status_code=401, detail="User không tồn tại")
            
        return user
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn")


@app.post(f"{settings.API_V1_PREFIX}/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(user_in: UserCreate):
    """Đăng ký tài khoản người dùng mới"""
    existing_user = await storage_service.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    
    user_dict = user_in.model_dump() if hasattr(user_in, 'model_dump') else user_in.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now().isoformat()
    
    new_user = await storage_service.create_user(user_dict)
    if not new_user:
        raise HTTPException(status_code=500, detail="Lỗi khi tạo tài khoản")
        
    new_user["id"] = str(new_user.get("_id", new_user["username"]))
    # Chuyển chuỗi thành datetime để trả về
    new_user["created_at"] = datetime.fromisoformat(new_user["created_at"])
    return new_user


@app.post(f"{settings.API_V1_PREFIX}/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Đăng nhập để nhận JWT token"""
    user = await storage_service.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai username hoặc password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"username": user["username"], "role": user.get("role", "user")}
    )
    user_resp = UserBase(**user)
    return {"access_token": access_token, "token_type": "bearer", "user": user_resp}




@app.on_event("startup")
async def startup_event():
    """Khởi tạo các dịch vụ khi ứng dụng chạy"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Model path: {settings.MODEL_PATH}")
    
    # Mô hình được tải trong ModelInference __init__
    if model_service.is_loaded():
        logger.info("✓ AI Model loaded successfully")
    else:
        logger.error("✗ Failed to load AI model")


@app.on_event("shutdown")
async def shutdown_event():
    """Dọn dẹp khi ứng dụng tắt"""
    logger.info("Shutting down application")


@app.get("/", tags=["Root"])
async def root():
    """Endpoint gốc"""
    return {
        "message": "MedAI Dermatology API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Endpoint kiểm tra sức khỏe hệ thống"""
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
async def predict(
    request: Request,
    file: UploadFile = File(..., description="Ảnh da cần chẩn đoán"),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Endpoint chính để upload ảnh và nhận dự đoán
    
    - **file**: File ảnh (JPG, PNG, HEIC) tối đa 10MB
    
    Returns thông tin dự đoán với độ tin cậy và khuyến nghị y tế
    """
    try:
        logger.info(f"--- INCOMING HEADERS for /api/v1/predict ---")
        for k, v in request.headers.items():
            logger.info(f"{k}: {v}")
        logger.info(f"--------------------------------------------")
        # Đọc nội dung file
        file_content = await file.read()
        
        # Kiểm tra tính hợp lệ của ảnh
        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Tạo định danh duy nhất cho chẩn đoán
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        diagnosis_id = f"DIAG-{timestamp_str}-{unique_id}"
        
        # Tiền xử lý ảnh
        logger.info(f"Preprocessing image for diagnosis {diagnosis_id}")
        preprocessed_img = preprocess_image(file_content)
        
        # Chạy AI dự đoán
        logger.info(f"Running AI prediction for {diagnosis_id}")
        predicted_class, confidence, all_predictions, critical_warning = model_service.predict(preprocessed_img)
        
        # Dọn dẹp bộ nhớ ảnh trung gian (Cần giữ file_content để lưu sau này)
        del preprocessed_img
        import gc
        gc.collect()
        
        # Lấy thông tin bệnh lý
        disease_name_vi = DISEASE_NAMES_VI.get(predicted_class, "Không xác định")
        disease_name_en = DISEASE_NAMES_EN.get(predicted_class, "Unknown")
        risk_level = RISK_LEVELS.get(predicted_class, "medium")
        risk_level_vi = RISK_LEVEL_VI.get(risk_level, "Trung bình")
        rec_text = RECOMMENDATIONS.get(predicted_class, "Vui lòng tư vấn bác sĩ chuyên khoa da liễu.")
        
        # Xây dựng đối tượng khuyến nghị có cấu trúc cho frontend
        recommendations = {
            "description": rec_text,
            "actions": [act.strip() for act in rec_text.split('.') if act.strip()],
            "urgency": "Cần khám ngay" if risk_level in ["high", "very_high", "critical"] else "Theo dõi thêm"
        }
        
        # Tạo đối tượng phản hồi
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
            critical_warning=critical_warning,
            timestamp=datetime.now()
        )
        
        # Lưu file ảnh đã upload
        try:
            await save_uploaded_image(file_content, diagnosis_id)
            logger.info(f"Saved image for {diagnosis_id}")
        except Exception as e:
            logger.warning(f"Failed to save image: {e}")

        # Cuối cùng mới giải phóng file_content
        del file_content
        gc.collect()
        
        # Lưu vào cơ sở dữ liệu (CHỈ KHI CÓ USER ĐĂNG NHẬP)
        if current_user:
            user_id = current_user.get("username")
            try:
                await storage_service.save_diagnosis(response, user_id=user_id)
                logger.info(f"Saved diagnosis {diagnosis_id} to database for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to save to database: {e}")
        else:
            logger.info(f"Diagnosis {diagnosis_id} not saved (user not logged in)")
        
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
    description="Lấy danh sách các chẩn đoán của người dùng hiện tại"
)
async def get_history(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """
    Lấy danh sách lịch sử chẩn đoán
    
    - **limit**: Số lượng record tối đa (mặc định 100)
    
    Returns danh sách các chẩn đoán đã thực hiện của user
    """
    try:
        user_id = current_user.get("username")
        user_role = current_user.get("role", "user")
        
        # Admin thấy toàn bộ lịch sử, user thường chỉ thấy của bản thân
        filter_user_id = None if user_role == "admin" else user_id
        
        records = await storage_service.get_all_diagnoses(limit=limit, user_id=filter_user_id)
        
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

@app.put(
    f"{settings.API_V1_PREFIX}/admin/users/{{username}}/role",
    tags=["Auth"],
    summary="Thay đổi quyền User (Admin only)"
)
async def update_user_role(
    username: str, 
    role: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cập nhật quyền của một người dùng. Chỉ có Admin mới được thực hiện.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện chức năng này"
        )
        
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role không hợp lệ. Phải là 'user' hoặc 'admin'"
        )
        
    success = await storage_service.update_user_role(username, role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng hoặc cập nhật thất bại"
        )
        
    return {"message": f"Cập nhật quyền của {username} thành {role} thành công"}


@app.get(
    f"{settings.API_V1_PREFIX}/admin/users",
    tags=["Admin"],
    summary="Lấy danh sách người dùng (Chỉ dành cho Admin)"
)
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền admin")
    return await storage_service.get_all_users()


@app.get(
    f"{settings.API_V1_PREFIX}/admin/stats",
    tags=["Admin"],
    summary="Lấy thống kê hệ thống (Chỉ dành cho Admin)"
)
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền admin")
    return await storage_service.get_dashboard_stats()


@app.get(
    f"{settings.API_V1_PREFIX}/history/{{diagnosis_id}}",
    response_model=PredictionResponse,
    tags=["History"],
    summary="Lấy chi tiết chẩn đoán",
    description="Lấy thông tin chi tiết của một chẩn đoán theo ID"
)
async def get_diagnosis(diagnosis_id: str, current_user: dict = Depends(get_current_user)):
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
        # Đọc nội dung file
        file_content = await file.read()
        
        # Tái sử dụng logic kiểm tra tính hợp lệ của ảnh
        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Tiền xử lý ảnh
        logger.info(f"Preprocessing preview for image: {file.filename}")
        
        # Xử lý ảnh qua các bước trung gian
        preprocessed_img, steps = preprocess_image(file_content, return_steps=True)
        
        # Loại bỏ chiều batch nếu có (1, H, W, C) -> (H, W, C)
        if len(preprocessed_img.shape) == 4:
            preprocessed_img = np.squeeze(preprocessed_img, axis=0)
        
        # Hàm hỗ trợ mã hóa ảnh thành luồng dữ liệu
        def encode_image(img_arr):
            if img_arr.dtype == np.float32 or img_arr.dtype == np.float64:
                if img_arr.max() <= 1.05:
                     img_arr = (img_arr * 255).astype(np.uint8)
                else:
                     img_arr = img_arr.astype(np.uint8)
            else:
                img_arr = img_arr.astype(np.uint8)
            
            # Chuyển đổi hệ màu RGB sang BGR
            img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            
            # Mã hóa sang dạng jpeg
            _, buffer = cv2.imencode('.jpg', img_bgr)
            return base64.b64encode(buffer).decode('utf-8')

        # Mã hóa ảnh sau khi xử lý thành chuỗi
        jpg_as_text = encode_image(preprocessed_img)
        
        # Mã hóa các bước trung gian
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


@app.post(
    f"{settings.API_V1_PREFIX}/feedback",
    tags=["Feedback"],
    summary="Gửi phản hồi cho AI (Chuyên gia)",
    description="Nhận phản hồi từ Bác sĩ/Admin về chẩn đoán của AI đúng hay sai"
)
async def submit_feedback(
    feedback: FeedbackRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint nhận phản hồi chuyên môn. 
    Yêu cầu quyền Bác sĩ (doctor) hoặc Quản trị viên (admin).
    """
    if current_user.get("role") not in ["doctor", "admin"]:
        logger.warning(f"Unauthorized feedback attempt by user: {current_user.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có Bác sĩ hoặc Quản trị viên mới có quyền gửi đánh giá chuyên môn"
        )
        
    try:
        feedback_dict = feedback.model_dump() if hasattr(feedback, 'model_dump') else feedback.dict()
        # Ghi lại ai là người đánh giá
        feedback_dict["doctor_id"] = current_user.get("username")
        
        success = await storage_service.save_feedback(feedback_dict)
        if success:
            return {"status": "success", "message": "Cảm ơn ý kiến chuyên môn của bạn!"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lưu phản hồi"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi gửi phản hồi: {str(e)}"
        )


@app.post(
    f"{settings.API_V1_PREFIX}/gradcam",
    response_model=GradCAMResponse,
    tags=["Explainability"],
    summary="Tạo GradCAM heatmap",
    description="Upload ảnh để tạo heatmap GradCAM giải thích vùng AI tập trung khi chẩn đoán"
)
async def gradcam(
    file: UploadFile = File(..., description="Ảnh da cần giải thích"),
    target_class: Optional[str] = None
):
    """
    Sinh GradCAM heatmap cho ảnh đã upload.

    - **file**: File ảnh (JPG, PNG) tối đa 10MB  
    - **target_class**: Tên class muốn giải thích (mặc định: class dự đoán)

    Returns heatmap đè lên ảnh gốc dưới dạng base64
    """
    from .utils.constants import CLASS_NAMES

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model chưa được load"
        )

    try:
        file_content = await file.read()

        # Kiểm tra tính hợp lệ
        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Tiền xử lý
        logger.info(f"GradCAM: preprocessing image {file.filename}")
        preprocessed_img = preprocess_image(file_content)

        # Xác định nhãn phân lớp (class) mục tiêu
        class_idx = None
        predicted_class_name = "N/A"
        
        if target_class and target_class in CLASS_NAMES:
            class_idx = CLASS_NAMES.index(target_class)
            predicted_class_name = target_class
            logger.info(f"GradCAM: Using provided target_class '{target_class}' (idx={class_idx})")
        else:
            # Chỉ chạy predict nếu không có target_class (để tiết kiệm RAM)
            logger.info("GradCAM: No target_class provided, running inference to find best class")
            predicted_class_name, _, _, _ = model_service.predict(preprocessed_img)
            class_idx = CLASS_NAMES.index(predicted_class_name)

        logger.info(f"GradCAM: generating for class '{predicted_class_name}' (idx={class_idx})")

        # Sinh ảnh heatmap đè lên
        heatmap_b64 = generate_gradcam_overlay(
            model=model_service._model,
            image_array=preprocessed_img,
            device=model_service._device,
            class_idx=class_idx
        )
        
        # Dọn dẹp bộ nhớ ảnh trung gian
        del file_content
        del preprocessed_img
        import gc
        gc.collect()

        return GradCAMResponse(
            heatmap_overlay=f"data:image/jpeg;base64,{heatmap_b64}",
            predicted_class=predicted_class_name,
            class_idx=class_idx
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GradCAM error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo GradCAM: {str(e)}"
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
