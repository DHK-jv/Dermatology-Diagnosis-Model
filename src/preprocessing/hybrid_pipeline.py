"""
Hybrid Preprocessing Pipeline
Kết hợp YOLO Segmentation + OpenCV để xử lý ảnh có hoặc không có mask
"""
import os
import sys
import numpy as np
import cv2
from typing import Optional, Union, Tuple

# Import existing preprocessing pipeline


# Import YOLO (with fallback)
# Import YOLO (with fallback)
try:
    try:
        from src.preprocessing.yolo_segmentor import YOLOSegmentor, YOLO_AVAILABLE
    except ImportError:
        try:
            from preprocessing.yolo_segmentor import YOLOSegmentor, YOLO_AVAILABLE
        except ImportError:
            from yolo_segmentor import YOLOSegmentor, YOLO_AVAILABLE
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  Warning: YOLO module not found")



class ImagePreprocessingPipeline:
    """
    Standard OpenCV-based Preprocessing Pipeline
    Includes: Segmentation (Crop) -> Resize -> Hair Removal -> Normalization
    """
    def __init__(self, target_size=(300, 300)):
        self.target_size = target_size

    def lesion_segmentation_and_crop(self, image, mask):
        """
        Crop vùng tổn thương dựa trên mask segmentation
        """
        # Validate inputs
        if image is None or image.size == 0:
            raise ValueError("Invalid image for segmentation")
        
        # Nếu mask None hoặc rỗng, trả về ảnh gốc
        if mask is None or mask.size == 0:
            print("⚠️  Warning: No mask provided, returning original image")
            return image
        
        try:
            # Nhị phân hóa mask
            _, binary_mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

            # Tìm contour tổn thương
            contours, _ = cv2.findContours(
                binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Nếu không tìm thấy mask → trả ảnh gốc
            if len(contours) == 0:
                print("⚠️  Warning: No contours found in mask, returning original image")
                return image

            # Lấy vùng tổn thương lớn nhất
            largest_contour = max(contours, key=cv2.contourArea)

            # Bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Validate bounding box
            if w < 10 or h < 10:
                print("⚠️  Warning: Detected region too small, returning original image")
                return image

            # Crop ROI
            cropped = image[y:y + h, x:x + w]

            return cropped
            
        except Exception as e:
            print(f"⚠️  Warning: Segmentation failed: {e}, returning original image")
            return image

    def resize_image(self, image):
        """ Bước 3: Thay đổi kích thước bằng OpenCV """
        # Nếu ảnh đã đúng kích thước thì trả về luôn
        if image.shape[:2] == self.target_size:
            return image
            
        # cv2.INTER_AREA là lựa chọn tốt nhất để giảm kích thước ảnh (Downsampling)
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)

    def hair_removal(self, image):
        """ 
        Bước 4: Thuật toán DullRazor
        Sử dụng: cv2.morphologyEx (BlackHat) và cv2.inpaint 
        """
        # Validate input
        if image is None or image.size == 0:
            raise ValueError("Invalid image for hair removal")
        
        # Check minimum size
        h, w = image.shape[:2]
        if h < 20 or w < 20:
            print(f"⚠️  Warning: Image too small ({h}x{w}), skipping hair removal")
            return image
        
        try:
            # 1. Chuyển sang ảnh xám
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 2. BlackHat để làm nổi bật sợi lông
            kernel_size = min(9, min(h, w) // 10)  # Adaptive kernel size
            kernel_size = max(3, kernel_size)  # At least 3x3
            if kernel_size % 2 == 0:  # Make sure it's odd
                kernel_size += 1
                
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
            
            # 3. Tạo mặt nạ sợi lông
            _, hair_mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
            
            # 4. Inpaint để bù đắp vùng da dưới sợi lông
            dst = cv2.inpaint(image, hair_mask, 1, cv2.INPAINT_TELEA)
            return dst
            
        except Exception as e:
            print(f"⚠️  Warning: Hair removal failed: {e}, returning original image")
            return image

    def pixel_normalization(self, image):
        """ Bước 5: Chuẩn hóa giá trị Pixel về [0, 1] """
        # 1. Chuyển kiểu dữ liệu sang float32 để tính toán chính xác
        image_float = image.astype(np.float32)
        
        # 2. Chia cho 255 để đưa giá trị về khoảng [0, 1]
        normalized_image = image_float / 255.0
        
        return normalized_image

    def process(self, image, mask, return_steps=False):
        """
        Thực thi pipeline trên ảnh đã load (numpy arrays)
        """
        steps = {}
        if return_steps:
            steps['original'] = image.copy()

        # Thực hiện các bước theo thứ tự
        img_cropped = self.lesion_segmentation_and_crop(image, mask) # Lesion Segmentation & Crop
        if return_steps:
            steps['cropped'] = img_cropped.copy()
        
        img_resized = self.resize_image(img_cropped)                 # Resize to 300x300
        if return_steps:
            steps['resized'] = img_resized.copy()
        
        img_hair_removed = self.hair_removal(img_resized)            # Hair Removal
        if return_steps:
            steps['hair_removed'] = img_hair_removed.copy()
        
        final_img = self.pixel_normalization(img_hair_removed)       # Pixel Value Normalization
        if return_steps:
            steps['normalized'] = final_img.copy()
        
        if return_steps:
            return final_img, steps
            
        return final_img

    def run(self, img_path, mask_path, return_steps=False):
        """ Thực thi toàn bộ quy trình từ đường dẫn file """
        img = cv2.imread(img_path) 
        if img is not None:
             img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert to RGB
        mask = cv2.imread(mask_path, 0) # Load mask ở dạng grayscale

        if img is None:
            raise ValueError(f"Could not read image at {img_path}")

        if return_steps:
            steps = {}
            steps['original'] = img.copy()
            
            img_cropped = self.lesion_segmentation_and_crop(img, mask)
            steps['cropped'] = img_cropped.copy()
            
            img_resized = self.resize_image(img_cropped)
            steps['resized'] = img_resized.copy()
            
            img_hair_removed = self.hair_removal(img_resized)
            steps['hair_removed'] = img_hair_removed.copy()
            
            final_img = self.pixel_normalization(img_hair_removed)
            steps['normalized'] = final_img.copy()
            
            return final_img, steps
        else:
            return self.process(img, mask)


class HybridPreprocessingPipeline:
    """
    Smart preprocessing pipeline tự chọn YOLO hoặc OpenCV
    
    Modes:
        - 'auto': Auto-detect (có mask → OpenCV, không mask → YOLO)
        - 'yolo': Force dùng YOLO segmentation  
        - 'opencv': Force dùng OpenCV (cần mask)
        - 'unet': Force dùng U-Net (nếu available)
    """
    
    def __init__(self, 
                 mode='auto', 
                 target_size=(300, 300),
                 yolo_model_path=None,
                 yolo_conf=0.5,
                 device='cpu'):
        """
        Initialize Hybrid Pipeline
        
        Args:
            mode (str): 'auto', 'yolo', 'opencv', hoặc 'unet'
            target_size (tuple): Kích thước output (H, W)
            yolo_model_path (str): Path đến YOLO model
            yolo_conf (float): YOLO confidence threshold
            device (str): 'cpu' hoặc 'cuda'
        """
        self.mode = mode
        self.target_size = target_size
        self.device = device
        
        # Initialize OpenCV pipeline (luôn có)
        self.opencv_pipeline = ImagePreprocessingPipeline(target_size=target_size)
        
        # Initialize YOLO (nếu mode cần)
        self.yolo_segmentor = None
        if mode in ['auto', 'yolo'] and YOLO_AVAILABLE:
            try:
                print(f"🤖 Initializing YOLO ({yolo_model_path})...")
                self.yolo_segmentor = YOLOSegmentor(
                    model_path=yolo_model_path,
                    conf_threshold=yolo_conf,
                    device=device
                )
                print("✅ YOLO initialized successfully")
            except Exception as e:
                print(f"⚠️  Failed to initialize YOLO: {e}")
                if mode == 'yolo':
                    raise RuntimeError("YOLO mode selected but YOLO not available!")
                else:
                    print("   Will fallback to OpenCV if no mask provided")
        
        # U-Net support (future)
        self.unet_model = None
        if mode == 'unet':
            print("⚠️  U-Net mode not implemented yet, falling back to YOLO")
            self.mode = 'auto'
    
    def process(self, image, mask=None, return_steps=False, verbose=True):
        """
        Process ảnh với auto mode selection
        
        Args:
            image (np.ndarray): Ảnh input (RGB hoặc BGR)
            mask (np.ndarray, optional): Mask có sẵn (grayscale 0-255)
            return_steps (bool): Return intermediate steps
            verbose (bool): Print progress
        
        Returns:
            np.ndarray: Processed image (normalized 0-1)
            hoặc tuple (processed_image, steps_dict) nếu return_steps=True
        """
        # Validate input
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")
        
        use_yolo = False
        result = None
        
        if self.mode == 'yolo':
            # Force YOLO
            if self.yolo_segmentor is None:
                raise RuntimeError("YOLO not available but mode='yolo'")
            use_yolo = True
            
        elif self.mode == 'opencv':
            # Force OpenCV
            if mask is None:
                raise ValueError("OpenCV mode requires mask input!")
            use_yolo = False
            
        elif self.mode == 'auto':
            # Auto-detect
            if mask is None:
                # Không có mask → dùng YOLO
                if self.yolo_segmentor is not None:
                    use_yolo = True
                    if verbose:
                        print("🔍 Auto mode: No mask provided, using YOLO")
                else:
                    raise ValueError("No mask provided and YOLO not available!")
            else:
                # Có mask → dùng OpenCV
                use_yolo = False
                if verbose:
                    print("🔍 Auto mode: Mask provided, using OpenCV")
        
        # Generate mask nếu dùng YOLO
        if use_yolo:
            if verbose:
                print("🤖 Generating mask with YOLO...")
            
            try:
                mask, confidence = self.yolo_segmentor.predict(
                    image, 
                    return_confidence=True
                )
                
                if verbose:
                    coverage = np.sum(mask > 0) / mask.size * 100
                    print(f"   YOLO Confidence: {confidence:.1%}")
                    print(f"   Mask coverage: {coverage:.1f}%")
                
                # Check nếu không detect được gì
                if confidence < 0.1:
                    print("⚠️  YOLO confidence very low, may not have detected lesion")
                    
            except Exception as e:
                print(f"❌ YOLO failed: {e}")
                raise RuntimeError("YOLO segmentation failed and no fallback mask available")
        
        # Process với OpenCV pipeline
        if verbose:
            print("🔧 Processing with OpenCV pipeline...")
        
        try:
            result = self.opencv_pipeline.process(
                image, 
                mask, 
                return_steps=return_steps
            )
            
            if verbose:
                print("✅ Processing completed")
            
            return result
            
        except Exception as e:
            print(f"❌ OpenCV processing failed: {e}")
            raise
    
    def run(self, image_path, mask_path=None, return_steps=False, verbose=True):
        """
        Process từ file paths
        
        Args:
            image_path (str): Path đến ảnh
            mask_path (str, optional): Path đến mask
            return_steps (bool): Return steps
            verbose (bool): Print progress
        
        Returns:
            np.ndarray: Processed image
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Hybrid Pipeline - Processing: {os.path.basename(image_path)}")
            print(f"Mode: {self.mode}")
            print(f"{'='*60}\n")
        
        # Load image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if verbose:
            print(f"📸 Image loaded: {image.shape}")
        
        # Load mask nếu có
        mask = None
        if mask_path:
            if os.path.exists(mask_path):
                mask = cv2.imread(mask_path, 0)  # Grayscale
                if verbose:
                    print(f"📄 Mask loaded: {mask.shape}")
            else:
                print(f"⚠️  Mask file not found: {mask_path}")
        
        # Process
        return self.process(image, mask, return_steps, verbose)
    
    def batch_process(self, image_paths, mask_paths=None, output_dir=None, verbose=False):
        """
        Process nhiều ảnh cùng lúc
        
        Args:
            image_paths (list): List of image paths
            mask_paths (list, optional): List of mask paths (same length)
            output_dir (str, optional): Directory để lưu ảnh đã xử lý
            verbose (bool): Print info cho mỗi ảnh
        
        Returns:
            list: List of processed images
        """
        if mask_paths is None:
            mask_paths = [None] * len(image_paths)
        
        if len(image_paths) != len(mask_paths):
            raise ValueError("image_paths and mask_paths must have same length")
        
        results = []
        
        print(f"\n🔄 Batch processing {len(image_paths)} images...")
        print(f"   Mode: {self.mode}")
        
        for i, (img_path, mask_path) in enumerate(zip(image_paths, mask_paths), 1):
            print(f"\n[{i}/{len(image_paths)}] Processing: {os.path.basename(img_path)}")
            
            try:
                processed = self.run(img_path, mask_path, verbose=verbose)
                results.append(processed)
                
                # Save nếu có output_dir
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(
                        output_dir, 
                        f"processed_{os.path.basename(img_path)}"
                    )
                    # Convert back to 0-255 để save
                    save_img = (processed * 255).astype(np.uint8)
                    cv2.imwrite(output_path, cv2.cvtColor(save_img, cv2.COLOR_RGB2BGR))
                    print(f"   ✅ Saved to: {output_path}")
                else:
                    print(f"   ✅ Processed successfully")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append(None)
        
        success_count = sum(1 for r in results if r is not None)
        print(f"\n✅ Batch processing completed: {success_count}/{len(image_paths)} successful")
        
        return results
    
    def get_stats(self):
        """Get pipeline statistics"""
        stats = {
            'mode': self.mode,
            'target_size': self.target_size,
            'yolo_available': self.yolo_segmentor is not None,
            'opencv_available': True,
            'device': self.device
        }
        return stats


# ============================================================================
# Test & Example Usage
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Hybrid Preprocessing Pipeline - Test")
    print("="*60)
    
    # Test 1: Với mask có sẵn (OpenCV mode)
    print("\n🧪 TEST 1: OpenCV mode (with mask)")
    print("-"*60)
    
    img_path = "../data/raw/images/ISIC_0024306.jpg"
    mask_path = "../data/masks/lesion/ISIC_0024306_segmentation.png"
    
    if os.path.exists(img_path) and os.path.exists(mask_path):
        pipeline_opencv = HybridPreprocessingPipeline(mode='opencv')
        
        try:
            result = pipeline_opencv.run(img_path, mask_path)
            print(f"\n✅ OpenCV mode test PASSED")
            print(f"   Output shape: {result.shape}")
            print(f"   Output range: [{result.min():.3f}, {result.max():.3f}]")
        except Exception as e:
            print(f"❌ OpenCV mode test FAILED: {e}")
    else:
        print("⚠️  Test files not found, skipping...")
    
    # Test 2: Không có mask (YOLO mode)
    print("\n\n🧪 TEST 2: Auto mode (no mask, use YOLO)")
    print("-"*60)
    
    if os.path.exists(img_path):
        pipeline_auto = HybridPreprocessingPipeline(mode='auto', device='cpu')
        
        try:
            result = pipeline_auto.run(img_path, mask_path=None)  # No mask
            print(f"\n✅ Auto mode (YOLO) test PASSED")
            print(f"   Output shape: {result.shape}")
            print(f"   Output range: [{result.min():.3f}, {result.max():.3f}]")
        except Exception as e:
            print(f"❌ Auto mode test FAILED: {e}")
    
    # Print stats
    print("\n\n📊 Pipeline Statistics:")
    print("-"*60)
    stats = pipeline_auto.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
