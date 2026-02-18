import cv2
import numpy as np
import torch
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class YOLOSegmentor:
    def __init__(self, model_path, conf_threshold=0.5, device='cpu'):
        if not YOLO_AVAILABLE:
            raise ImportError("Ultralytics YOLO is not installed.")
        
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.device = device
        # Force device if possible, though YOLO usually handles it
        # self.model.to(device) 

    def predict(self, image, return_confidence=False, verbose=False):
        """
        Run YOLO inference.
        Args:
            image: numpy array (H, W, 3) used by YOLO
            return_confidence: bool
            verbose: bool
        Returns:
            mask: numpy array (H, W) or None
            confidence: float (optional)
        """
        # Run inference
        results = self.model.predict(
            source=image,
            conf=self.conf_threshold,
            device=self.device,
            verbose=verbose,
            retina_masks=True,
            stream=False 
        )

        if not results or len(results) == 0:
            return (None, 0.0) if return_confidence else None
        
        result = results[0]
        
        # Check if masks detected
        if result.masks is None:
            return (None, 0.0) if return_confidence else None
        
        # Get mask with highest confidence
        # result.boxes.conf is a tensor of confidences
        # result.masks.data is a tensor of masks (N, H, W)
        
        if len(result.boxes) == 0:
             return (None, 0.0) if return_confidence else None

        # Find max confidence index
        max_idx = torch.argmax(result.boxes.conf).item()
        confidence = result.boxes.conf[max_idx].item()
        
        # Extract Mask
        # Ultralytics masks return (N, H, W), we need to resize to original image shape if not retina
        # But retina_masks=True usually gives good masks. 
        # result.masks.data is likely on GPU if device=cuda
        
        raw_mask = result.masks.data[max_idx].cpu().numpy()
        
        # Resize mask to original image size if needed
        # raw_mask shape might differ from image shape depending on YOLO version
        img_h, img_w = image.shape[:2]
        
        if raw_mask.shape != (img_h, img_w):
            mask = cv2.resize(raw_mask, (img_w, img_h), interpolation=cv2.INTER_LINEAR)
        else:
            mask = raw_mask
            
        # Binarize
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        if return_confidence:
            return mask, confidence
        return mask
