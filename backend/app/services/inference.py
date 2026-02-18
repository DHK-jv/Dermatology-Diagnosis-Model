"""
AI Model inference service (PyTorch Version)
Handles model loading and prediction
"""
import os
import torch
import torch.nn.functional as F
from torchvision import transforms, models
import numpy as np
from typing import Dict, Tuple
import logging

from ..config import settings
from ..utils.constants import CLASS_NAMES

logger = logging.getLogger(__name__)


class ModelInference:
    """Singleton class for model inference (PyTorch)"""
    
    _instance = None
    _model = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize and load model"""
        if self._model is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.load_model()
    
    def load_model(self):
        """Load the trained EfficientNet model (.pth)"""
        try:
            logger.info(f"Loading PyTorch model from {settings.MODEL_PATH}")
            logger.info(f"Device: {self._device}")
            
            # Create model architecture using torchvision
            # The checkpoint was trained with torchvision.models.efficientnet_b4
            self._model = models.efficientnet_b4(weights=None)
            
            # Modify classifier head to match our 24 classes
            num_ftrs = self._model.classifier[1].in_features
            self._model.classifier[1] = torch.nn.Linear(num_ftrs, len(CLASS_NAMES))
            
            # Load checkpoint (nested structure)
            # weights_only=False needed for PyTorch 2.6+ with numpy objects
            checkpoint = torch.load(
                str(settings.MODEL_PATH), 
                map_location=self._device,
                weights_only=False
            )
            
            # Extract model state from checkpoint
            if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
                state_dict = checkpoint['model_state']
                val_acc = checkpoint.get('val_acc', None)
                if val_acc is not None:
                    logger.info(f"Loaded checkpoint with Val Acc: {val_acc:.4f}")
            else:
                # Fallback for direct state dict (backward compatibility)
                state_dict = checkpoint
                logger.info("Loaded direct state dict (no metadata)")
            
            # Load state dict
            self._model.load_state_dict(state_dict)
            
            # Set to eval mode!
            self._model.to(self._device)
            self._model.eval()
            
            logger.info(f"PyTorch Model loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {str(e)}")
            # Don't raise error here, let it fail on predict or status check 
            # so the app can still start (just unhealthy)
    
    def predict(self, image_array: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        """
        Run prediction on preprocessed image
        
        Args:
            image_array: Preprocessed image array (1, 380, 380, 3) - Values 0-255 float/uint8
            
        Returns:
            Tuple of (predicted_class, confidence, all_predictions_dict)
        """
        if self._model is None:
            self.load_model()
            if self._model is None:
                raise RuntimeError("Model chưa được load")
        
        try:
            # 1. Prepare Input Tensor
            # Remove batch dim: (1, 380, 380, 3) -> (380, 380, 3)
            img = image_array[0]
            
            # Convert to Tensor (C, H, W) and scale 0-1
            # Current img is float (0-255), so we divide by 255.0
            img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            
            # Normalize (ImageNet stats)
            normalize = transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
            img_tensor = normalize(img_tensor)
            
            # Add batch dimension: (1, C, H, W)
            input_tensor = img_tensor.unsqueeze(0).to(self._device)
            
            # 2. Inference
            with torch.no_grad():
                outputs = self._model(input_tensor)
                probabilities = F.softmax(outputs, dim=1)[0]
            
            # 3. Process Results
            # Move to CPU numpy
            probs_np = probabilities.cpu().numpy()
            
            # Get predicted class
            predicted_idx = np.argmax(probs_np)
            predicted_class = CLASS_NAMES[predicted_idx]
            confidence = float(probs_np[predicted_idx])
            
            # Create dict of all predictions (sorted by confidence)
            all_predictions = {
                CLASS_NAMES[i]: float(probs_np[i])
                for i in range(len(CLASS_NAMES))
            }
            all_predictions = dict(
                sorted(all_predictions.items(), key=lambda x: x[1], reverse=True)
            )
            
            logger.info(
                f"Prediction complete: {predicted_class} "
                f"(confidence: {confidence:.3f})"
            )
            
            return predicted_class, confidence, all_predictions
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise RuntimeError(f"Lỗi khi chạy AI prediction: {str(e)}")
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model is not None


# Create global instance
model_service = ModelInference()
