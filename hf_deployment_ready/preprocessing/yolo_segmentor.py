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
        import gc
        
        # Run inference in no_grad mode to save memory
        with torch.no_grad():
            results = self.model.predict(
                source=image,
                conf=self.conf_threshold,
                device=self.device,
                verbose=verbose,
                retina_masks=True,
                imgsz=1024,
                stream=False 
            )

        if not results or len(results) == 0:
            del results
            gc.collect()
            return (None, 0.0) if return_confidence else None
        
        result = results[0]
        
        # Check if masks detected
        if result.masks is None:
            del results
            gc.collect()
            return (None, 0.0) if return_confidence else None
        
        if len(result.boxes) == 0:
            del results
            gc.collect()
            return (None, 0.0) if return_confidence else None

        # Find max confidence index
        max_idx = torch.argmax(result.boxes.conf).item()
        confidence = result.boxes.conf[max_idx].item()
        
        # Extract Mask
        raw_mask = result.masks.data[max_idx].cpu().numpy()
        
        # Resize mask to original image size if needed
        img_h, img_w = image.shape[:2]
        
        if raw_mask.shape != (img_h, img_w):
            mask = cv2.resize(raw_mask, (img_w, img_h), interpolation=cv2.INTER_LINEAR)
        else:
            mask = raw_mask
            
        # Binarize
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        # Explicit cleanup of large YOLO objects
        del results
        del result
        gc.collect()
        
        if return_confidence:
            return mask, confidence
        return mask
