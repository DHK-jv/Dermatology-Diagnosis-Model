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



# Khởi tạo pipeline một lần để tái sử dụng quá trình tiền xử lý
try:
    # Import trực tiếp (PYTHONPATH xử lý việc phân giải đường dẫn trong Docker và Local)
    # Chúng ta dựa vào PYTHONPATH=/app (Docker) hoặc chạy từ thư mục gốc dự án (Local)
    from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline
    
    pipeline = HybridPreprocessingPipeline(
        mode=settings.PREPROCESSING_MODE,
        target_size=settings.IMAGE_SIZE,
        device='cpu'  # Sử dụng CPU cho backend để tiết kiệm tài nguyên
    )
    PIPELINE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Failed to load HybridPreprocessingPipeline: {e}")
    PIPELINE_AVAILABLE = False


def preprocess_image(image_bytes: bytes, return_steps: bool = False):
    """
    Tiền xử lý ảnh cho đầu vào mô hình sử dụng Hybrid Pipeline
    
    Args:
        image_bytes: Raw image bytes (ảnh gốc)
        return_steps: Có trả về các bước trung gian hay không
        
    Returns:
        Nếu return_steps=False:
            Mảng ảnh đã qua tiền xử lý, sẵn sàng cho mô hình (kích thước: (1, 380, 380, 3))
        Nếu return_steps=True:
            Tuple (img_array, steps_dict)
    """
    # Mở ảnh
    img = Image.open(io.BytesIO(image_bytes))
    
    # Chuyển đổi sang hệ màu RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Chuyển sang mảng numpy cho pipeline
    img_np = np.array(img)
    
    if PIPELINE_AVAILABLE:
        try:
            # Sử dụng pipeline tiền xử lý (YOLO tự động tạo mask, không có mask thủ công)
            if return_steps:
                result, steps = pipeline.process(img_np, return_steps=True, verbose=False)
                
                # Thêm chiều batch vào kết quả
                result_batch = np.expand_dims(result, axis=0)
                
                # Chuẩn hóa các bước trung gian về 0-255 nếu đang ở dạng 0-1
                normalized_steps = {}
                for key, val in steps.items():
                    if val.dtype == np.float32 or val.dtype == np.float64:
                        if val.max() <= 1.05:
                            val = (val * 255).astype(np.uint8)
                        else:
                            val = val.astype(np.uint8)
                    else:
                        val = val.astype(np.uint8)
                    normalized_steps[key] = val
                    
                return result_batch * 255.0, normalized_steps
            else:
                result = pipeline.process(img_np, return_steps=False, verbose=False)
                return np.expand_dims(result, axis=0) * 255.0
                
        except Exception as e:
            print(f"Hybrid Pipeline failed: {e}. Attempting pure OpenCV fallback.")
            
            # Dự phòng bằng pipeline OpenCV (bỏ qua segmentation nếu không có mask, nhưng vẫn xóa lông)
            # Sử dụng instance opencv_pipeline bên trong hybrid pipeline nếu có
            try:
                if return_steps:
                    result, steps = pipeline.opencv_pipeline.process(img_np, return_steps=True)
                    
                    # Thêm chiều batch
                    result_batch = np.expand_dims(result, axis=0)
                    
                    # Chuẩn hóa các bước trung gian
                    normalized_steps = {}
                    for key, val in steps.items():
                         if val.dtype == np.float32 or val.dtype == np.float64:
                             if val.max() <= 1.05:
                                  val = (val * 255).astype(np.uint8)
                             else:
                                  val = val.astype(np.uint8)
                         else:
                             val = val.astype(np.uint8)
                         normalized_steps[key] = val
                         
                    return result_batch * 255.0, normalized_steps
                else:
                    result = pipeline.opencv_pipeline.process(img_np)
                    return np.expand_dims(result, axis=0) * 255.0
            except Exception as e2:
                print(f"OpenCV fallback failed: {e2}. Using basic resize.")
    
    # Dự phòng cuối cùng: Thay đổi kích thước (Resize) cơ bản
    img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
    img_array = np.array(img_resized, dtype=np.float32)
    # img_array = img_array / 255.0 # Kiểm tra xem mô hình có cần phép tính này không
    
    if return_steps:
        # Trả về các bước trung gian cơ bản cho trường hợp dự phòng
        steps = {
            'original': np.array(img),
            'resized': np.array(img_resized)
        }
        return np.expand_dims(img_array, axis=0), steps
        
    return np.expand_dims(img_array, axis=0)


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
