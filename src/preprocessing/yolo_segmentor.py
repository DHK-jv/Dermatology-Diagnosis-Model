"""
YOLO Segmentation Module
Auto-generate masks từ ảnh da không có mask sẵn
"""
import os
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  Warning: ultralytics not installed. Install with: pip install ultralytics")


class YOLOSegmentor:
    """
    Wrapper cho YOLOv8 Segmentation model
    Tự động phát hiện và tạo mask cho vùng tổn thương da
    """
    
    def __init__(self, model_path='yolov8n-seg.pt', conf_threshold=0.5, device='cpu'):
        """
        Initialize YOLO Segmentor
        
        Args:
            model_path (str): Path đến model YOLO (.pt file)
                             - 'yolov8n-seg.pt': Nano (nhanh, nhẹ)
                             - 'yolov8s-seg.pt': Small
                             - 'path/to/custom_model.pt': Custom trained model
            conf_threshold (float): Confidence threshold (0-1)
            device (str): 'cpu' hoặc 'cuda'
        """
        if not YOLO_AVAILABLE:
            raise ImportError("ultralytics not installed! Run: pip install ultralytics")
        
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.device = device
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model với error handling"""
        try:
            print(f"Loading YOLO model: {self.model_path}...")
            self.model = YOLO(self.model_path)
            
            # Set device
            if self.device == 'cuda':
                try:
                    self.model.to('cuda')
                    print("✅ YOLO running on GPU")
                except Exception as e:
                    print(f"⚠️  GPU not available, falling back to CPU: {e}")
                    self.device = 'cpu'
                    self.model.to('cpu')
            else:
                self.model.to('cpu')
                print("✅ YOLO running on CPU")
            
            print(f"✅ YOLO model loaded successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}")
    
    def predict(self, image, return_confidence=False):
        """
        Dự đoán và tạo mask từ ảnh
        
        Args:
            image (np.ndarray): Ảnh input (BGR hoặc RGB)
            return_confidence (bool): Có return confidence không
        
        Returns:
            np.ndarray: Binary mask (0-255, grayscale)
            hoặc tuple (mask, confidence) nếu return_confidence=True
        """
        if self.model is None:
            raise RuntimeError("Model not loaded!")
        
        # Validate input
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")
        
        try:
            # Run inference
            results = self.model.predict(
                image, 
                conf=self.conf_threshold,
                verbose=False  # Tắt verbose output
            )
            
            # Get first result (assume 1 image)
            result = results[0]
            
            # Check if có detect được object
            if result.masks is None or len(result.masks) == 0:
                print("⚠️  YOLO: No lesion detected, returning empty mask")
                h, w = image.shape[:2]
                empty_mask = np.zeros((h, w), dtype=np.uint8)
                
                if return_confidence:
                    return empty_mask, 0.0
                return empty_mask
            
            # Get mask với highest confidence
            masks = result.masks.data.cpu().numpy()  # Shape: (N, H, W)
            confidences = result.boxes.conf.cpu().numpy()  # Shape: (N,)
            
            # Select mask với confidence cao nhất
            best_idx = np.argmax(confidences)
            best_mask = masks[best_idx]
            best_conf = float(confidences[best_idx])
            
            # Resize mask về kích thước ảnh gốc
            h, w = image.shape[:2]
            mask_resized = cv2.resize(best_mask, (w, h), interpolation=cv2.INTER_LINEAR)
            
            # Convert to binary (0 hoặc 255)
            mask_binary = (mask_resized > 0.5).astype(np.uint8) * 255
            
            if return_confidence:
                return mask_binary, best_conf
            
            return mask_binary
            
        except Exception as e:
            print(f"❌ YOLO prediction error: {e}")
            # Return empty mask on error
            h, w = image.shape[:2]
            empty_mask = np.zeros((h, w), dtype=np.uint8)
            
            if return_confidence:
                return empty_mask, 0.0
            return empty_mask
    
    def predict_multi(self, image, min_conf=None):
        """
        Detect multiple lesions (nếu có nhiều vùng tổn thương)
        
        Args:
            image (np.ndarray): Ảnh input
            min_conf (float): Minimum confidence (optional, dùng self.conf_threshold nếu None)
        
        Returns:
            list[dict]: List of detected lesions, mỗi item có:
                - 'mask': Binary mask
                - 'confidence': Confidence score
                - 'bbox': Bounding box [x, y, w, h]
        """
        if min_conf is None:
            min_conf = self.conf_threshold
        
        try:
            results = self.model.predict(image, conf=min_conf, verbose=False)
            result = results[0]
            
            if result.masks is None or len(result.masks) == 0:
                return []
            
            masks = result.masks.data.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
            
            lesions = []
            h, w = image.shape[:2]
            
            for i in range(len(masks)):
                mask = cv2.resize(masks[i], (w, h), interpolation=cv2.INTER_LINEAR)
                mask_binary = (mask > 0.5).astype(np.uint8) * 255
                
                # Convert xyxy to xywh
                x1, y1, x2, y2 = boxes[i]
                bbox = [int(x1), int(y1), int(x2-x1), int(y2-y1)]
                
                lesions.append({
                    'mask': mask_binary,
                    'confidence': float(confidences[i]),
                    'bbox': bbox
                })
            
            # Sort by confidence (cao nhất trước)
            lesions.sort(key=lambda x: x['confidence'], reverse=True)
            
            return lesions
            
        except Exception as e:
            print(f"❌ YOLO multi-prediction error: {e}")
            return []
    
    def visualize(self, image, mask=None, save_path=None):
        """
        Visualize kết quả segmentation
        
        Args:
            image (np.ndarray): Ảnh gốc
            mask (np.ndarray): Mask (optional, sẽ predict nếu None)
            save_path (str): Path để lưu ảnh (optional)
        
        Returns:
            np.ndarray: Ảnh đã overlay mask
        """
        if mask is None:
            mask, conf = self.predict(image, return_confidence=True)
            print(f"Predicted with confidence: {conf:.2f}")
        
        # Tạo overlay
        overlay = image.copy()
        
        # Tô màu xanh lá vùng mask
        overlay[mask > 0] = [0, 255, 0]  # Green
        
        # Blend
        result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
        
        if save_path:
            cv2.imwrite(save_path, result)
            print(f"✅ Visualization saved to: {save_path}")
        
        return result


# ============================================================================
# Test và Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("YOLO Segmentation Module - Test")
    print("="*60)
    
    # Check availability
    if not YOLO_AVAILABLE:
        print("❌ ultralytics not installed!")
        print("Install with: pip install ultralytics")
        sys.exit(1)
    
    # Test với ảnh mẫu
    test_image_path = "data/raw/images/ISIC_0024306.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"⚠️  Test image not found: {test_image_path}")
        print("Skipping test...")
    else:
        print(f"\n📸 Loading test image: {test_image_path}")
        img = cv2.imread(test_image_path)
        
        if img is not None:
            print(f"   Image shape: {img.shape}")
            
            # Initialize YOLO
            print("\n🤖 Initializing YOLO Segmentor...")
            try:
                segmentor = YOLOSegmentor(
                    model_path='yolov8n-seg.pt',  # Will auto-download if not exists
                    conf_threshold=0.25,
                    device='cpu'  # Use 'cuda' if GPU available
                )
                
                # Predict mask
                print("\n🔍 Predicting mask...")
                mask, confidence = segmentor.predict(img, return_confidence=True)
                
                print(f"   Mask shape: {mask.shape}")
                print(f"   Confidence: {confidence:.2%}")
                print(f"   Mask coverage: {np.sum(mask > 0) / mask.size:.2%}")
                
                # Visualize
                print("\n🎨 Creating visualization...")
                viz = segmentor.visualize(img, mask)
                
                # Save
                output_dir = "reports/figures/yolo_test"
                os.makedirs(output_dir, exist_ok=True)
                cv2.imwrite(f"{output_dir}/yolo_mask.png", mask)
                cv2.imwrite(f"{output_dir}/yolo_overlay.png", viz)
                
                print(f"✅ Results saved to: {output_dir}/")
                print("\n✅ YOLO Segmentor test completed successfully!")
                
            except Exception as e:
                print(f"\n❌ Error during test: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Failed to load image")
    
    print("\n" + "="*60)
