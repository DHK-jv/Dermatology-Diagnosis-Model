"""
Dịch vụ tiền xử lý ảnh
Xử lý việc kiểm tra, thay đổi kích thước và chuẩn hóa ảnh cho đầu vào mô hình

FIX LOG:
- BUG #5: Luôn lưu ảnh gốc (original_raw) vào steps trước khi bất kỳ resize nào xảy ra
- BUG #6: Thêm retry logic sau khoảng thời gian chờ thay vì chặn vĩnh viễn
"""
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import io
import threading
import asyncio
import time

from ..config import settings

# ---------------------------------------------------------------------------
# Hằng số nội bộ
# ---------------------------------------------------------------------------
_NORMALIZE_THRESHOLD = 1.05   # Ngưỡng phân biệt ảnh đã normalize [0,1] hay chưa
_PIPELINE_RETRY_INTERVAL = 300  # ✅ FIX BUG #6: Cho phép retry sau 5 phút


# ---------------------------------------------------------------------------
# Singleton pipeline (module-level cache + thread-safe lock)
# ---------------------------------------------------------------------------
_pipeline_lock = threading.Lock()
_cached_pipeline = None
_pipeline_load_attempted = False
_pipeline_last_failure_time = 0.0  # ✅ FIX BUG #6: Theo dõi thời điểm thất bại


def _get_pipeline():
    """
    Trả về pipeline đã được khởi tạo từ trước (Singleton + thread-safe).

    - Lần đầu: load YOLO model vào RAM, cache lại trong `_cached_pipeline`.
    - Các lần sau: trả về ngay, không tốn thêm ~3s load model.
    - ✅ FIX BUG #6: Nếu load thất bại, cho phép retry sau _PIPELINE_RETRY_INTERVAL giây
      thay vì chặn vĩnh viễn (tránh trường hợp lỗi tạm thời khi khởi động server).
    """
    global _cached_pipeline, _pipeline_load_attempted, _pipeline_last_failure_time

    # Fast-path: pipeline đã sẵn sàng
    if _cached_pipeline is not None:
        return _cached_pipeline

    with _pipeline_lock:
        # Double-checked locking
        if _cached_pipeline is not None:
            return _cached_pipeline

        if _pipeline_load_attempted:
            # ✅ FIX BUG #6: Cho phép retry sau khoảng thời gian chờ
            elapsed = time.time() - _pipeline_last_failure_time
            if elapsed < _PIPELINE_RETRY_INTERVAL:
                remaining = int(_PIPELINE_RETRY_INTERVAL - elapsed)
                print(f"⏳ Pipeline load skipped (failed {int(elapsed)}s ago, retry in {remaining}s)")
                return None
            else:
                # Reset để thử lại
                print("🔄 Retrying pipeline load after previous failure...")
                _pipeline_load_attempted = False

        _pipeline_load_attempted = True
        try:
            from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline

            yolo_model_path = settings.BASE_DIR / "ml_models" / "best_hair_seg.pt"
            if not yolo_model_path.exists():
                yolo_model_path = settings.BASE_DIR / "ml_models" / "yolov8n-seg.pt"

            _cached_pipeline = HybridPreprocessingPipeline(
                mode=settings.PREPROCESSING_MODE,
                target_size=settings.IMAGE_SIZE,
                yolo_model_path=str(yolo_model_path) if yolo_model_path.exists() else None,
                device='cpu',
            )
            # ✅ Reset thời gian thất bại sau khi load thành công
            _pipeline_last_failure_time = 0.0
            _pipeline_load_attempted = False
            print("✅ HybridPreprocessingPipeline loaded and cached.")
        except Exception as e:
            _pipeline_last_failure_time = time.time()
            print(f"⚠️  Failed to load HybridPreprocessingPipeline: {e}")
            _cached_pipeline = None

    return _cached_pipeline


def release_pipeline() -> None:
    """
    Giải phóng pipeline khỏi RAM (dùng khi shutdown server hoặc khi cần
    thu hồi bộ nhớ theo yêu cầu vận hành).
    """
    global _cached_pipeline, _pipeline_load_attempted, _pipeline_last_failure_time
    import gc

    with _pipeline_lock:
        if _cached_pipeline is not None:
            if hasattr(_cached_pipeline, 'yolo_segmentor') and _cached_pipeline.yolo_segmentor:
                del _cached_pipeline.yolo_segmentor
            del _cached_pipeline
            _cached_pipeline = None
            _pipeline_load_attempted = False
            _pipeline_last_failure_time = 0.0
            gc.collect()
            print("🧹 Pipeline released from memory.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_image(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Kiểm tra file ảnh tải lên.

    Args:
        file_content: Dữ liệu file (raw bytes)
        filename:     Tên file gốc

    Returns:
        Tuple (is_valid, error_message)
    """
    extension = filename.lower().rsplit('.', 1)[-1]
    if extension not in settings.ALLOWED_EXTENSIONS:
        return False, (
            f"Định dạng file không hợp lệ. "
            f"Chỉ chấp nhận: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        return False, f"File quá lớn. Kích thước tối đa: {settings.MAX_IMAGE_SIZE_MB}MB"

    try:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()
        return True, ""
    except Exception as e:
        return False, f"File không phải là ảnh hợp lệ: {str(e)}"


# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------
def _normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Chuyển mảng float [0,1] hoặc uint8 [0,255] về uint8 [0,255]."""
    if arr.dtype in (np.float32, np.float64):
        return (arr * 255).astype(np.uint8) if arr.max() <= _NORMALIZE_THRESHOLD else arr.astype(np.uint8)
    return arr.astype(np.uint8)


def _ensure_batch_scale(batch: np.ndarray) -> np.ndarray:
    """Đảm bảo batch trả về có giá trị pixel trong [0, 255]."""
    if batch.max() <= _NORMALIZE_THRESHOLD:
        return batch * 255.0
    return batch


def _fallback_preprocess(img_np: np.ndarray, return_steps: bool, original_np: np.ndarray = None, enhancement_enabled: bool = False):
    """
    Tiền xử lý dự phòng: resize vuông (padding đen) bằng HybridPreprocessingPipeline mode 'none'.

    ✅ FIX BUG #5: Nhận thêm original_np để lưu vào steps['original_raw']
    """
    try:
        from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline
        fallback_pipeline = HybridPreprocessingPipeline(
            mode='opencv',
            target_size=settings.IMAGE_SIZE
        )
        if return_steps:
            result, steps = fallback_pipeline.opencv_pipeline.process(
                img_np, mask=None, return_steps=True, enhancement_enabled=enhancement_enabled
            )
            result_batch = _ensure_batch_scale(np.expand_dims(result, axis=0))
            normalized_steps = {k: _normalize_to_uint8(v) for k, v in steps.items()}
            # ✅ FIX BUG #5: Luôn lưu ảnh gốc vào steps để GradCAM dùng
            if original_np is not None:
                normalized_steps['original_raw'] = original_np.copy()
            return result_batch, normalized_steps
        else:
            result = fallback_pipeline.opencv_pipeline.process(
                img_np, mask=None, return_steps=False, enhancement_enabled=enhancement_enabled
            )
            return _ensure_batch_scale(np.expand_dims(result, axis=0))
    except Exception as e:
        print(f"⚠️ Fallback pipeline failed: {e}. Last resort: PIL resize.")
        img = Image.fromarray(img_np)
        img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img_resized, dtype=np.float32)
        result_batch = np.expand_dims(img_array, axis=0)
        if return_steps:
            steps = {'resized': img_array.astype(np.uint8)}
            if original_np is not None:
                steps['original_raw'] = original_np.copy()
            return result_batch, steps
        return result_batch


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def preprocess_image(image_bytes: bytes, return_steps: bool = False, preprocessing_enabled: bool = True):
    """
    Tiền xử lý ảnh toàn diện.

    Args:
        image_bytes:           Dữ liệu ảnh thô (bytes)
        return_steps:          Nếu True, trả về thêm dict các bước trung gian
        preprocessing_enabled: Nếu False, bỏ qua các bước nâng cao, chỉ resize.

    Returns:
        np.ndarray batch shape (1, H, W, 3), pixel [0,255]  — hoặc
        Tuple(batch, steps_dict) nếu return_steps=True

    ✅ FIX BUG #5: steps luôn chứa 'original_raw' là ảnh gốc chưa qua resize
                   để GradCAM có thể overlay lên ảnh gốc thực sự.
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_np = np.array(img)

    # ✅ FIX BUG #5: Lưu ảnh gốc TRƯỚC BẤT KỲ bước nào (kể cả limit_resolution)
    original_np = img_np.copy()

    # Nếu tắt tiền xử lý → fallback resize-only (nhưng vẫn kèm original_raw)
    if not preprocessing_enabled or settings.PREPROCESSING_MODE.lower() == "none":
        return _fallback_preprocess(img_np, return_steps, original_np=original_np)

    pipeline = _get_pipeline()

    if pipeline is None:
        print("⚠️  Pipeline unavailable, falling back to resize-only.")
        return _fallback_preprocess(img_np, return_steps, original_np=original_np)

    try:
        if return_steps:
            result, steps = pipeline.process(img_np, return_steps=True, enhancement_enabled=preprocessing_enabled)
            result_batch = _ensure_batch_scale(np.expand_dims(result, axis=0))
            normalized_steps = {k: _normalize_to_uint8(v) if isinstance(v, np.ndarray) else v for k, v in steps.items()}
            # ✅ FIX BUG #5: Gắn ảnh gốc vào steps
            normalized_steps['original_raw'] = original_np
            return result_batch, normalized_steps
        else:
            result = pipeline.process(img_np, return_steps=False, enhancement_enabled=preprocessing_enabled)
            return _ensure_batch_scale(np.expand_dims(result, axis=0))

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}. Falling back to resize-only.")
        return _fallback_preprocess(img_np, return_steps, original_np=original_np)


async def save_uploaded_image(file_content: bytes, diagnosis_id: str) -> Path:
    """
    Lưu ảnh đã tải lên vào ổ đĩa cứng (non-blocking).

    Args:
        file_content:  Ảnh dạng byte nguyên thủy
        diagnosis_id:  Định danh duy nhất cho chẩn đoán

    Returns:
        Đường dẫn tới file ảnh đã lưu
    """
    def _write() -> Path:
        filepath = settings.UPLOAD_DIR / f"{diagnosis_id}.jpg"
        img = Image.open(io.BytesIO(file_content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(filepath, 'JPEG', quality=95)
        return filepath

    return await asyncio.to_thread(_write)
