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



# Initialize pipeline once to reuse the preprocessing pipeline
try:
    # Append project root to path so we can import src
    import sys
    sys.path.append(str(settings.PROJECT_ROOT))
    from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline
    
    pipeline = HybridPreprocessingPipeline(
        mode='auto',
        target_size=settings.IMAGE_SIZE,
        device='cpu'  # Use CPU for backend to save resources
    )
    PIPELINE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Failed to load HybridPreprocessingPipeline: {e}")
    PIPELINE_AVAILABLE = False


def preprocess_image(image_bytes: bytes, return_steps: bool = False):
    """
    Preprocess image for model input using Hybrid Pipeline
    
    Args:
        image_bytes: Raw image bytes
        return_steps: Whether to return intermediate steps
        
    Returns:
        If return_steps=False:
            Preprocessed image array ready for model (shape: (1, 380, 380, 3))
        If return_steps=True:
            Tuple (img_array, steps_dict)
    """
    # Open image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to numpy array for pipeline
    img_np = np.array(img)
    
    if PIPELINE_AVAILABLE:
        try:
            # Use the preprocessing pipeline (YOLO auto mask, no manual mask)
            if return_steps:
                result, steps = pipeline.process(img_np, return_steps=True, verbose=False)
                
                # Add batch dimension to result
                result_batch = np.expand_dims(result, axis=0)
                
                # Normalize steps back to 0-255 if they are 0-1
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
            
            # Fallback to OpenCV pipeline (skips segmentation if no mask, but does Hair Removal)
            # Use the opencv_pipeline instance inside the hybrid pipeline if available
            try:
                if return_steps:
                    result, steps = pipeline.opencv_pipeline.process(img_np, return_steps=True)
                    
                    # Add batch dimension
                    result_batch = np.expand_dims(result, axis=0)
                    
                    # Normalize steps
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
    
    # Ultimate Fallback: Basic Resize
    img_resized = img.resize(settings.IMAGE_SIZE, Image.Resampling.LANCZOS)
    img_array = np.array(img_resized, dtype=np.float32)
    # img_array = img_array / 255.0 # Check if model needs this
    
    if return_steps:
        # Return basic steps for fallback
        steps = {
            'original': np.array(img),
            'resized': np.array(img_resized)
        }
        return np.expand_dims(img_array, axis=0), steps
        
    return np.expand_dims(img_array, axis=0)


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
