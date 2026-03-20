"""
Dịch vụ tiền xử lý ảnh
Xử lý việc kiểm tra, thay đổi kích thước và chuẩn hóa ảnh cho đầu vào mô hình
"""
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import io
import threading
import asyncio

from ..config import settings

# ---------------------------------------------------------------------------
# Hằng số nội bộ
# ---------------------------------------------------------------------------
_NORMALIZE_THRESHOLD = 1.05   # Ngưỡng phân biệt ảnh đã normalize [0,1] hay chưa


# ---------------------------------------------------------------------------
# Singleton pipeline (module-level cache + thread-safe lock)
# ---------------------------------------------------------------------------
_pipeline_lock = threading.Lock()
_cached_pipeline = None          # Pipeline dùng chung cho mọi request
_pipeline_load_attempted = False # Tránh retry vô hạn nếu load thất bại


def _get_pipeline():
    """
    Trả về pipeline đã được khởi tạo từ trước (Singleton + thread-safe).

    - Lần đầu: load YOLO model vào RAM, cache lại trong `_cached_pipeline`.
    - Các lần sau: trả về ngay, không tốn thêm ~3s load model.
    - Nếu load thất bại một lần, đánh dấu `_pipeline_load_attempted = True`
      để không retry mỗi request (tránh log spam + chậm).
    """
    global _cached_pipeline, _pipeline_load_attempted

    # Fast-path: pipeline đã sẵn sàng
    if _cached_pipeline is not None:
        return _cached_pipeline

    # Slow-path: chỉ một thread được phép khởi tạo tại một thời điểm
    with _pipeline_lock:
        # Double-checked locking: kiểm tra lại sau khi có lock
        if _cached_pipeline is not None:
            return _cached_pipeline

        if _pipeline_load_attempted:
            # Đã thất bại trước đó → không thử lại
            return None

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
            print("✅ HybridPreprocessingPipeline loaded and cached.")
        except Exception as e:
            print(f"⚠️  Failed to load HybridPreprocessingPipeline: {e}")
            _cached_pipeline = None

    return _cached_pipeline


def release_pipeline() -> None:
    """
    Giải phóng pipeline khỏi RAM (dùng khi shutdown server hoặc khi cần
    thu hồi bộ nhớ theo yêu cầu vận hành).

    Không nên gọi trong flow xử lý request thông thường.
    """
    global _cached_pipeline, _pipeline_load_attempted
    import gc

    with _pipeline_lock:
        if _cached_pipeline is not None:
            if hasattr(_cached_pipeline, 'yolo_segmentor') and _cached_pipeline.yolo_segmentor:
                del _cached_pipeline.yolo_segmentor
            del _cached_pipeline
            _cached_pipeline = None
            _pipeline_load_attempted = False
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
    # Kiểm tra đuôi mở rộng
    extension = filename.lower().rsplit('.', 1)[-1]
    if extension not in settings.ALLOWED_EXTENSIONS:
        return False, (
            f"Định dạng file không hợp lệ. "
            f"Chỉ chấp nhận: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Kiểm tra kích thước file
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        return False, f"File quá lớn. Kích thước tối đa: {settings.MAX_IMAGE_SIZE_MB}MB"

    # Xác minh nội dung thực sự là ảnh
    # Lưu ý: img.verify() làm file handle không dùng được nữa → mở riêng
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


def _fallback_preprocess(img_np: np.ndarray, return_steps: bool):
    """
    Tiền xử lý dự phòng cưỡng bức: sử dụng HybridPreprocessingPipeline ở chế độ 'none'
    để thực hiện resize vuông (padding đen) thay vì kéo giãn ảnh (PIL stretch).
    """
    try:
        from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline
        # Khởi tạo pipeline "nhẹ" chỉ để resize
        fallback_pipeline = HybridPreprocessingPipeline(
            mode='opencv', # Không dùng YOLO
            target_size=settings.IMAGE_SIZE
        )
        # Chèn mask=None để kích hoạt resize-only
        if return_steps:
            result, steps = fallback_pipeline.opencv_pipeline.process(img_np, mask=None, return_steps=True)
            result_batch = _ensure_batch_scale(np.expand_dims(result, axis=0))
            normalized_steps = {k: _normalize_to_uint8(v) for k, v in steps.items()}
            return result_batch, normalized_steps
        else:
            result = fallback_pipeline.opencv_pipeline.process(img_np, mask=None, return_steps=False)
            return _ensure_batch_scale(np.expand_dims(result, axis=0))
    except Exception as e:
        print(f"⚠️ Fallback pipeline failed: {e}. Last resort: PIL resize.")
        # Trường hợp xấu nhất: dùng lại logic cũ (dễ bị stretch)
        img = Image.fromarray(img_np)
        img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img_resized, dtype=np.float32)
        result_batch = np.expand_dims(img_array, axis=0)
        return result_batch


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def preprocess_image(image_bytes: bytes, return_steps: bool = False, preprocessing_enabled: bool = True):
    """
    Tiền xử lý ảnh toàn diện.

    Args:
        image_bytes:  Dữ liệu ảnh thô (bytes)
        return_steps: Nếu True, trả về thêm dict các bước trung gian
        preprocessing_enabled: Nếu False, bỏ qua các bước nâng cao (Hair removal/Segment), chỉ resize.

    Returns:
        np.ndarray batch shape (1, H, W, 3), pixel [0,255]  — hoặc
        Tuple(batch, steps_dict) nếu return_steps=True
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_np = np.array(img)

    # Nếu tắt tiền xử lý (hoặc mode='none'), dùng fallback (chỉ resize vuông)
    if not preprocessing_enabled or settings.PREPROCESSING_MODE.lower() == "none":
        return _fallback_preprocess(img_np, return_steps)

    pipeline = _get_pipeline()

    if pipeline is None:
        print("⚠️  Pipeline unavailable, falling back to resize-only.")
        return _fallback_preprocess(img_np, return_steps)

    try:
        if return_steps:
            result, steps = pipeline.process(img_np, return_steps=True, verbose=False, enhancement_enabled=preprocessing_enabled)
            result_batch = _ensure_batch_scale(np.expand_dims(result, axis=0))
            normalized_steps = {k: _normalize_to_uint8(v) for k, v in steps.items()}
            return result_batch, normalized_steps
        else:
            result = pipeline.process(img_np, return_steps=False, verbose=False, enhancement_enabled=preprocessing_enabled)
            return _ensure_batch_scale(np.expand_dims(result, axis=0))

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}. Falling back to resize-only.")
        return _fallback_preprocess(img_np, return_steps)


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

    # Chạy I/O blocking trong thread pool để không block event loop
    return await asyncio.to_thread(_write)
