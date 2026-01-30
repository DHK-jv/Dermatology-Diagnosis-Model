"""
Image preprocessing service
Handles image validation, resizing, and normalization for model input
"""
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple
import io

from ..config import settings


def validate_image(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate uploaded image file
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    extension = filename.lower().split('.')[-1]
    if extension not in settings.ALLOWED_EXTENSIONS:
        return False, f"Định dạng file không hợp lệ. Chỉ chấp nhận: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        return False, f"File quá lớn. Kích thước tối đa: {settings.MAX_IMAGE_SIZE_MB}MB"
    
    # Try to open as image
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()  # Verify it's actually an image
        return True, ""
    except Exception as e:
        return False, f"File không phải là ảnh hợp lệ: {str(e)}"


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image for model input
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Preprocessed image array ready for model (shape: (1, 300, 300, 3))
    """
    # Open image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB (in case of RGBA or grayscale)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize to model input size
    img = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    # Convert to numpy array
    img_array = np.array(img, dtype=np.float32)
    
    # Normalize to [0, 1] range (EfficientNet expects this)
    # kwjv: Removed normalization because model expects [0, 255]
    # img_array = img_array / 255.0
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


async def save_uploaded_image(file_content: bytes, diagnosis_id: str) -> Path:
    """
    Save uploaded image to disk
    
    Args:
        file_content: Raw image bytes
        diagnosis_id: Unique diagnosis ID
        
    Returns:
        Path to saved image
    """
    # Create filename
    filename = f"{diagnosis_id}.jpg"
    filepath = settings.UPLOAD_DIR / filename
    
    # Open and save as JPEG (standard format)
    img = Image.open(io.BytesIO(file_content))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.save(filepath, 'JPEG', quality=95)
    
    return filepath
