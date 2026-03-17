"""
Dịch vụ tiền xử lý ảnh
Xử lý việc kiểm tra, thay đổi kích thước và chuẩn hóa ảnh cho đầu vào mô hình
"""
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple
import io
import sys

from ..config import settings


def validate_image(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Kiểm tra file ảnh tải lên
    
    Args:
        file_content: Dữ liệu file (raw bytes)
        filename: Tên file gốc
        
    Returns:
        Tuple chứa (is_valid, error_message) - (hợp lệ hay không, thông báo lỗi)
    """
    # Kiểm tra đuôi mở rộng của file
    extension = filename.lower().split('.')[-1]
    if extension not in settings.ALLOWED_EXTENSIONS:
        return False, f"Định dạng file không hợp lệ. Chỉ chấp nhận: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    # Kiểm tra kích thước file
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        return False, f"File quá lớn. Kích thước tối đa: {settings.MAX_IMAGE_SIZE_MB}MB"
    
    # Thử mở file dưới dạng ảnh
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()  # Xác minh đó thực sự là một file ảnh
        return True, ""
    except Exception as e:
        return False, f"File không phải là ảnh hợp lệ: {str(e)}"



# Lazy loading functions
def _get_pipeline():
    """Tạo pipeline tiền xử lý mới (Lazy Load)"""
    try:
        from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline
        yolo_model_path = settings.BASE_DIR / "ml_models" / "best_hair_seg.pt"
        if not yolo_model_path.exists():
            yolo_model_path = settings.BASE_DIR / "ml_models" / "yolov8n-seg.pt"
        
        return HybridPreprocessingPipeline(
            mode=settings.PREPROCESSING_MODE,
            target_size=settings.IMAGE_SIZE,
            yolo_model_path=str(yolo_model_path) if yolo_model_path.exists() else None,
            device='cpu'
        )
    except Exception as e:
        print(f"⚠️ Failed to load HybridPreprocessingPipeline: {e}")
        return None


def preprocess_image(image_bytes: bytes, return_steps: bool = False):
    """
    Tiền xử lý ảnh toàn diện với cơ chế Lazy Loading để tiết kiệm RAM
    """
    import gc
    
    # Mở ảnh
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_np = np.array(img)

    # Nếu muốn tắt toàn bộ tiền xử lý (chỉ resize)
    if settings.PREPROCESSING_MODE.lower() == "none":
        img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img_resized, dtype=np.float32)
        result_batch = np.expand_dims(img_array, axis=0)
        if return_steps:
            normalized_steps = {
                'original': np.array(img),
                'resized': np.array(img_resized),
                'normalized': np.array(img_resized)
            }
            return result_batch, normalized_steps
        return result_batch
    
    # Khởi tạo pipeline TẠI CHỖ (Lazy Load)
    pipeline = _get_pipeline()
    
    result_batch = None
    normalized_steps = None
    
    if pipeline:
        try:
            if return_steps:
                result, steps = pipeline.process(img_np, return_steps=True, verbose=False)
                result_batch = np.expand_dims(result, axis=0)
                if result.max() <= 1.05:
                    result_batch = result_batch * 255.0
                
                normalized_steps = {}
                for key, val in steps.items():
                    if val.dtype in [np.float32, np.float64]:
                        val = (val * 255).astype(np.uint8) if val.max() <= 1.05 else val.astype(np.uint8)
                    else:
                        val = val.astype(np.uint8)
                    normalized_steps[key] = val
            else:
                result = pipeline.process(img_np, return_steps=False, verbose=False)
                result_batch = np.expand_dims(result, axis=0)
                if result.max() <= 1.05:
                    result_batch = result_batch * 255.0
        except Exception as e:
            print(f"Hybrid Pipeline execution failed: {e}")
        finally:
            # GIẢI PHÓNG YOLO NGAY LẬP TỨC
            if hasattr(pipeline, 'yolo_segmentor') and pipeline.yolo_segmentor:
                del pipeline.yolo_segmentor.model
                del pipeline.yolo_segmentor
            del pipeline
            gc.collect()
            print("🧹 YOLO memory cleared after preprocessing")

    # Dự phòng nếu pipeline thất bại hoặc không có
    if result_batch is None:
        img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img_resized, dtype=np.float32)
        result_batch = np.expand_dims(img_array, axis=0)
        if return_steps:
            normalized_steps = {
                'original': np.array(img),
                'resized': np.array(img_resized),
                'normalized': np.array(img_resized)
            }
    
    if return_steps:
        return result_batch, normalized_steps
    return result_batch


async def save_uploaded_image(file_content: bytes, diagnosis_id: str) -> Path:
    """
    Lưu ảnh đã tải lên vào ổ đĩa cứng
    
    Args:
        file_content: Ảnh dạng byte nguyên thủy
        diagnosis_id: Định danh duy nhất cho chẩn đoán
        
    Returns:
        Đường dẫn tới file ảnh đã lưu
    """
    # Tạo tên file
    filename = f"{diagnosis_id}.jpg"
    filepath = settings.UPLOAD_DIR / filename
    
    # Mở và lưu dưới định dạng JPEG (định dạng chuẩn)
    img = Image.open(io.BytesIO(file_content))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.save(filepath, 'JPEG', quality=95)
    
    return filepath
