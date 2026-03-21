"""
Ứng dụng FastAPI chính
MedAI Dermatology - Backend API chẩn đoán tổn thương da
"""
import gc
import logging
import os
import uuid
import base64
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt

from .config import settings
from .models.schemas import (
    DiagnosisHistory,
    FeedbackRequest,
    GradCAMResponse,
    HealthResponse,
    HistoryListResponse,
    PredictionResponse,
    PreviewResponse,
    Token,
    UserBase,
    UserCreate,
    UserResponse,
)
from .services.gradcam import generate_gradcam_overlay
from .services.image_preprocessing import (
    preprocess_image,
    save_uploaded_image,
    validate_image,
)
from .services.inference import model_service
from .services.cleanup import run_cleanup_periodically
from .services.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    verify_password,
)
from .services.storage import storage_service
from .utils.constants import (
    CLASS_NAMES,
    DISEASE_NAMES_EN,
    DISEASE_NAMES_VI,
    MEDICAL_LOGO,
    RECOMMENDATIONS,
    RISK_LEVEL_VI,
    RISK_LEVELS,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (thay thế @app.on_event deprecated từ FastAPI 0.93)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Model path: {settings.MODEL_PATH}")
    if model_service.is_loaded():
        logger.info("✓ AI Model loaded successfully")
    else:
        logger.error("✗ Failed to load AI model")

    # Start Background Cleanup Task
    import asyncio
    asyncio.create_task(run_cleanup_periodically(interval_seconds=3600))
    logger.info("✓ Background Cleanup Task started (hourly)")

    yield  # Ứng dụng chạy

    # ── Shutdown ──
    logger.info("Shutting down application")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API chẩn đoán bệnh da bằng AI sử dụng EfficientNet-B4",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Gắn thư mục uploads để phục vụ ảnh tĩnh
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ---------------------------------------------------------------------------
# CORS — đọc từ biến môi trường, hỗ trợ mọi nền tảng (HF Spaces, Docker…)
# ---------------------------------------------------------------------------
# CORS — nạp từ cấu hình mặc định (localhost) + biến môi trường
_cors_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
_cors_origins = settings.CORS_ORIGINS.copy()

if _cors_origins_env:
    _cors_origins.extend([o.strip() for o in _cors_origins_env.split(",") if o.strip()])

# Thêm domain chính nếu chưa có
if "https://khangjv.id.vn" not in _cors_origins:
    _cors_origins.append("https://khangjv.id.vn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials="*" not in _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
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


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme_optional),
) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")

        user = await storage_service.get_user_by_username(username=username)
        if user is None:
            raise HTTPException(status_code=401, detail="User không tồn tại")
        return user
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn")


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post(
    f"{settings.API_V1_PREFIX}/auth/register",
    response_model=UserResponse,
    tags=["Auth"],
)
async def register(user_in: UserCreate):
    """Đăng ký tài khoản người dùng mới"""
    if await storage_service.get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    user_dict = user_in.model_dump() if hasattr(user_in, "model_dump") else user_in.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now().isoformat()

    new_user = await storage_service.create_user(user_dict)
    if not new_user:
        raise HTTPException(status_code=500, detail="Lỗi khi tạo tài khoản")

    new_user["id"] = str(new_user.get("_id", new_user["username"]))
    new_user["created_at"] = datetime.fromisoformat(new_user["created_at"])
    return new_user


@app.post(
    f"{settings.API_V1_PREFIX}/auth/login",
    response_model=Token,
    tags=["Auth"],
)
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
    return {"access_token": access_token, "token_type": "bearer", "user": UserBase(**user)}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Endpoint kiểm tra sức khỏe hệ thống"""
    return HealthResponse(
        status="healthy",
        model_loaded=model_service.is_loaded(),
        version=settings.VERSION,
    )


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------
@app.post(
    f"{settings.API_V1_PREFIX}/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Upload ảnh và nhận chẩn đoán",
    description="Upload ảnh da để AI phân tích và đưa ra chẩn đoán bệnh",
)
async def predict(
    request: Request,
    file: UploadFile = File(..., description="Ảnh da cần chẩn đoán"),
    preprocessing: bool = Form(True, description="Bật/Tắt tiền xử lý ảnh nâng cao"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Endpoint chính: upload ảnh → nhận kết quả chẩn đoán AI.

    - **file**: JPG / PNG / HEIC, tối đa 10 MB
    """
    # Ghi log ở mức DEBUG để tránh rò rỉ Authorization header vào log production
    logger.debug("Incoming headers for /predict: %s", dict(request.headers))

    try:
        file_content = await file.read()

        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Tạo ID chẩn đoán
        diagnosis_id = f"DIAG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

        # Tiền xử lý + dự đoán
        logger.info(f"Preprocessing image for {diagnosis_id} (enabled={preprocessing})")
        preprocessed_img, steps = preprocess_image(file_content, return_steps=True, preprocessing_enabled=preprocessing)
        crop_box = steps.get('crop_box') # [x1, y1, x2, y2] if cropped

        logger.info(f"Running AI prediction for {diagnosis_id}")
        predicted_class, confidence, all_predictions, critical_warning = model_service.predict(
            preprocessed_img
        )

        # Giải phóng bộ nhớ ảnh trung gian ngay sau predict
        del preprocessed_img
        gc.collect()

        # Tra cứu metadata bệnh
        risk_level = RISK_LEVELS.get(predicted_class, "medium")
        rec_text = RECOMMENDATIONS.get(predicted_class, "Vui lòng tư vấn bác sĩ chuyên khoa da liễu.")

        response = PredictionResponse(
            diagnosis_id=diagnosis_id,
            predicted_class=predicted_class,
            disease_name_vi=DISEASE_NAMES_VI.get(predicted_class, "Không xác định"),
            disease_name_en=DISEASE_NAMES_EN.get(predicted_class, "Unknown"),
            confidence=confidence,
            confidence_percent=f"{confidence * 100:.1f}%",
            risk_level=risk_level,
            risk_level_vi=RISK_LEVEL_VI.get(risk_level, "Trung bình"),
            all_predictions=all_predictions,
            recommendations={
                "description": rec_text,
                "actions": [a.strip() for a in rec_text.split(".") if a.strip()],
                "urgency": (
                    "Cần khám ngay"
                    if risk_level in {"high", "very_high", "critical"}
                    else "Theo dõi thêm"
                ),
            },
            critical_warning=critical_warning,
            preprocessing_applied=preprocessing,
            crop_box=crop_box,
            timestamp=datetime.now(),
        )

        # Lưu ảnh (giữ file_content đến đây)
        try:
            await save_uploaded_image(file_content, diagnosis_id)
            logger.info(f"Saved image for {diagnosis_id}")
        except Exception as e:
            logger.warning(f"Failed to save image: {e}")
        finally:
            del file_content
            gc.collect()

        # Lưu lịch sử chẩn đoán (chỉ khi đăng nhập)
        if current_user:
            try:
                await storage_service.save_diagnosis(response, user_id=current_user["username"])
                logger.info(f"Saved diagnosis {diagnosis_id} for user {current_user['username']}")
            except Exception as e:
                logger.warning(f"Failed to save diagnosis to DB: {e}")
        else:
            logger.info(f"Diagnosis {diagnosis_id} not saved (anonymous user)")

        logger.info(f"Prediction complete: {diagnosis_id} → {predicted_class} ({confidence:.2%})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý ảnh: {e}",
        )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
@app.get(
    f"{settings.API_V1_PREFIX}/history",
    response_model=HistoryListResponse,
    tags=["History"],
    summary="Lấy lịch sử chẩn đoán",
)
async def get_history(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Lấy danh sách lịch sử chẩn đoán (admin thấy tất cả, user thường chỉ thấy của mình)."""
    try:
        user_id = current_user["username"]
        filter_user_id = None if current_user.get("role") == "admin" else user_id
        records = await storage_service.get_all_diagnoses(limit=limit, user_id=filter_user_id)
        return HistoryListResponse(total=len(records), records=records)
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy lịch sử: {e}",
        )


@app.get(
    f"{settings.API_V1_PREFIX}/history/{{diagnosis_id}}",
    response_model=PredictionResponse,
    tags=["History"],
    summary="Lấy chi tiết chẩn đoán",
)
async def get_diagnosis(
    diagnosis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Lấy chi tiết một chẩn đoán theo ID."""
    try:
        diagnosis = await storage_service.get_diagnosis_by_id(diagnosis_id)
        if diagnosis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy chẩn đoán với ID: {diagnosis_id}",
            )
        return diagnosis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diagnosis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin chẩn đoán: {e}",
        )


# ---------------------------------------------------------------------------
# Preview preprocessing
# ---------------------------------------------------------------------------
def _encode_image_to_base64(img_arr: Optional[np.ndarray]) -> str:
    """Chuyển numpy array (RGB) thành chuỗi base64 JPEG."""
    if img_arr is None:
        return ""
    if not isinstance(img_arr, np.ndarray):
        img_arr = np.array(img_arr)

    # Chuẩn hóa về uint8
    if img_arr.dtype in (np.float32, np.float64):
        img_arr = (img_arr * 255).astype(np.uint8) if img_arr.max() <= 1.05 else img_arr.astype(np.uint8)
    else:
        img_arr = img_arr.astype(np.uint8)

    # Đảm bảo 3 kênh RGB
    if img_arr.ndim == 2:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
    elif img_arr.ndim == 3 and img_arr.shape[2] == 4:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2RGB)

    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer).decode("utf-8")


@app.post(
    f"{settings.API_V1_PREFIX}/predict/preview",
    response_model=PreviewResponse,
    tags=["Prediction"],
    summary="Xem trước tiền xử lý ảnh",
    description="Upload ảnh và nhận lại ảnh đã qua tiền xử lý (segmentation, hair removal, resize)",
)
async def preview_preprocessing(
    file: UploadFile = File(..., description="Ảnh da cần xem trước"),
    preprocessing: bool = Form(True, description="Bật/Tắt tiền xử lý nâng cao"),
):
    """Trả về ảnh đã xử lý và các bước trung gian dưới dạng base64."""
    try:
        file_content = await file.read()

        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        logger.info(f"Preview preprocessing for: {file.filename} (enabled={preprocessing})")
        preprocessed_img, steps = preprocess_image(file_content, return_steps=True, preprocessing_enabled=preprocessing)

        # (1, H, W, C) → (H, W, C)
        if preprocessed_img.ndim == 4:
            preprocessed_img = np.squeeze(preprocessed_img, axis=0)

        encoded_steps = {
            key: f"data:image/jpeg;base64,{_encode_image_to_base64(img)}"
            for key, img in (steps or {}).items()
        }

        return PreviewResponse(
            processed_image=f"data:image/jpeg;base64,{_encode_image_to_base64(preprocessed_img)}",
            steps=encoded_steps,
            preprocessing_applied=preprocessing,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý ảnh preview: {e}",
        )


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
@app.post(
    f"{settings.API_V1_PREFIX}/feedback",
    tags=["Feedback"],
    summary="Gửi phản hồi cho AI (Chuyên gia)",
)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Nhận phản hồi từ Bác sĩ/Admin. Yêu cầu quyền doctor hoặc admin."""
    if current_user.get("role") not in {"doctor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có Bác sĩ hoặc Quản trị viên mới có quyền gửi đánh giá chuyên môn",
        )
    try:
        feedback_dict = (
            feedback.model_dump() if hasattr(feedback, "model_dump") else feedback.dict()
        )
        feedback_dict["doctor_id"] = current_user["username"]

        if not await storage_service.save_feedback(feedback_dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lưu phản hồi",
            )
        return {"status": "success", "message": "Cảm ơn ý kiến chuyên môn của bạn!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi gửi phản hồi: {e}",
        )


# ---------------------------------------------------------------------------
# GradCAM
# ---------------------------------------------------------------------------
@app.post(
    f"{settings.API_V1_PREFIX}/gradcam",
    response_model=GradCAMResponse,
    tags=["Explainability"],
    summary="Tạo GradCAM heatmap",
    description="Upload ảnh để tạo heatmap GradCAM giải thích vùng AI tập trung khi chẩn đoán",
)
async def gradcam(
    file: UploadFile = File(..., description="Ảnh da cần giải thích"),
    target_class: Optional[str] = None,
    preprocessing: bool = Form(True, description="Bật/Tắt tiền xử lý ảnh nâng cao"),
    layer_offset: int = Form(-2, description="Offset Layer của GradCAM (mặc định -2)")
):
    """
    Sinh GradCAM heatmap cho ảnh đã upload.

    - **target_class**: Tên class muốn giải thích (mặc định: class dự đoán cao nhất)
    """
    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model chưa được load",
        )
    try:
        file_content = await file.read()

        is_valid, error_msg = validate_image(file_content, file.filename)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # ✅ FIX BUG #2: Lưu ảnh gốc TRƯỚC khi bất kỳ bước preprocess nào chạy.
        # Ảnh gốc này sẽ được dùng để overlay heatmap lên đúng vị trí thực tế,
        # không phải ảnh đã bị crop/resize/letterbox bởi pipeline.
        from PIL import Image as _PIL_Image
        import io as _io
        _raw_pil = _PIL_Image.open(_io.BytesIO(file_content))
        if _raw_pil.mode != 'RGB':
            _raw_pil = _raw_pil.convert('RGB')
        original_img_np = np.array(_raw_pil)  # (H_orig, W_orig, 3) — kích thước thực tế người dùng upload
        del _raw_pil

        logger.info(f"GradCAM: preprocessing {file.filename} (enabled={preprocessing}), original size={original_img_np.shape[:2]}")
        preprocessed_img, steps = preprocess_image(file_content, return_steps=True, preprocessing_enabled=preprocessing)

        # Xác định class mục tiêu
        if target_class and target_class in CLASS_NAMES:
            class_idx = CLASS_NAMES.index(target_class)
            predicted_class_name = target_class
            logger.info(f"GradCAM: target_class='{target_class}' (idx={class_idx})")
        else:
            logger.info("GradCAM: no target_class, running inference")
            predicted_class_name, _, _, _ = model_service.predict(preprocessed_img)
            class_idx = CLASS_NAMES.index(predicted_class_name)

        logger.info(f"GradCAM: generating for '{predicted_class_name}' (idx={class_idx})")

        # ✅ FIX BUG #2: Truyền original_img_np → GradCAM sẽ upscale heatmap lên
        # kích thước ảnh gốc và overlay đúng vị trí, thay vì overlay trên ảnh đã preprocess.
        crop_box_data = steps.get('crop_box')
        
        # ✅ V3.0: Lấy danh sách tên bệnh để phân tích Top-K
        class_names = [DISEASE_NAMES_EN.get(k, k) for k in CLASS_NAMES]

        # Generate Grad-CAM overlay (Hỗ trợ Geometric Coordinate mapping)
        heatmap_uri, analysis_dict = generate_gradcam_overlay(
            model=model_service._model,
            img_preprocessed=preprocessed_img,
            original_for_display=original_img_np,
            target_class=class_idx,
            mask=steps.get('mask_final'),
            crop_box=crop_box_data,
            class_names=class_names, # ✅ V3.0 New feature
            layer_offset=layer_offset, # ✅ V3.0 New feature
            comparison_view=False,
            include_colorbar=True,
        )

        # Encode ảnh preprocessed (kích thước model) để UI có thể so sánh nếu cần
        encode_img = preprocessed_img[0]
        if encode_img.max() <= 1.05:
            encode_img = encode_img * 255.0
        encode_img = encode_img.astype(np.uint8)
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(encode_img, cv2.COLOR_RGB2BGR))
        preprocessed_b64 = base64.b64encode(buffer).decode('utf-8')

        # Encode ảnh gốc để trả về frontend (panel "Ảnh Gốc" hiển thị đúng)
        _, orig_buffer = cv2.imencode('.jpg', cv2.cvtColor(original_img_np, cv2.COLOR_RGB2BGR),
                                      [cv2.IMWRITE_JPEG_QUALITY, 95])
        original_b64 = base64.b64encode(orig_buffer).decode('utf-8')

        del file_content, preprocessed_img, original_img_np
        gc.collect()

        return GradCAMResponse(
            heatmap_overlay=f"data:image/jpeg;base64,{heatmap_uri}",
            predicted_class=predicted_class_name,
            class_idx=class_idx,
            # ✅ FIX BUG #2: preprocessed_image vẫn trả về để debug nếu cần,
            # nhưng UI bây giờ ưu tiên hiển thị original_image làm nền so sánh.
            preprocessed_image=f"data:image/jpeg;base64,{preprocessed_b64}",
            # ✅ Thêm trường original_image để frontend luôn có ảnh gốc đúng
            original_image=f"data:image/jpeg;base64,{original_b64}",
            analysis=analysis_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GradCAM error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo GradCAM: {e}",
        )


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------
@app.put(
    f"{settings.API_V1_PREFIX}/admin/users/{{username}}/role",
    tags=["Auth"],
    summary="Thay đổi quyền User (Admin only)",
)
async def update_user_role(
    username: str,
    role: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền")

    if role not in {"user", "doctor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role không hợp lệ. Phải là 'user', 'doctor' hoặc 'admin'",
        )

    if not await storage_service.update_user_role(username, role):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng hoặc cập nhật thất bại",
        )
    return {"message": f"Cập nhật quyền của {username} thành {role} thành công"}


@app.get(
    f"{settings.API_V1_PREFIX}/admin/users",
    tags=["Admin"],
    summary="Lấy danh sách người dùng (Admin only)",
)
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền admin")
    return await storage_service.get_all_users()


@app.get(
    f"{settings.API_V1_PREFIX}/admin/stats",
    tags=["Admin"],
    summary="Lấy thống kê hệ thống (Admin only)",
)
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền admin")
    return await storage_service.get_dashboard_stats()


# ---------------------------------------------------------------------------
# Frontend static files (đặt cuối cùng để không chặn route API)
# ---------------------------------------------------------------------------
def _mount_frontend() -> None:
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
        "/app/frontend",
    ]
    for path in candidates:
        if os.path.exists(path):
            app.mount("/", StaticFiles(directory=path, html=True), name="frontend")
            logger.info(f"✓ Frontend mounted from {path}")
            return
    logger.warning("Frontend directory not found — skipping static mount")


_mount_frontend()


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not os.environ.get("PORT"),
        log_level="info",
    )
