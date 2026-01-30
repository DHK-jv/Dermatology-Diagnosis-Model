"""
AI Model inference service
Handles model loading and prediction
"""
import os
# Force CPU-only mode to avoid GPU/CUDA compatibility issues
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging

import tensorflow as tf
import numpy as np
from typing import Dict, Tuple
import logging

from ..config import settings
from ..utils.constants import CLASS_NAMES

logger = logging.getLogger(__name__)


class ModelInference:
    """Singleton class for model inference"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize and load model"""
        if self._model is None:
            self.load_model()
    
    def load_model(self):
        """Load the trained EfficientNet model"""
        try:
            logger.info(f"Loading model from {settings.MODEL_PATH}")
            
            # Disable GPU if not needed (for faster CPU inference on small batches)
            # Uncomment if you want CPU-only
            # tf.config.set_visible_devices([], 'GPU')
            
            self._model = tf.keras.models.load_model(
                str(settings.MODEL_PATH),
                compile=False  # We don't need training
            )
            
            logger.info(f"Model loaded successfully. Input shape: {self._model.input_shape}")
            logger.info(f"Model output shape: {self._model.output_shape}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise RuntimeError(f"Không thể load model AI: {str(e)}")
    
    def predict(self, image_array: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        """
        Run prediction on preprocessed image
        
        Args:
            image_array: Preprocessed image array (1, 300, 300, 3)
            
        Returns:
            Tuple of (predicted_class, confidence, all_predictions_dict)
        """
        if self._model is None:
            raise RuntimeError("Model chưa được load")
        
        try:
            # Run inference
            predictions = self._model.predict(image_array, verbose=0)
            
            # Get probabilities for all classes
            probabilities = predictions[0]  # Remove batch dimension
            
            # Get predicted class
            predicted_idx = np.argmax(probabilities)
            predicted_class = CLASS_NAMES[predicted_idx]
            confidence = float(probabilities[predicted_idx])
            
            # Create dict of all predictions (sorted by confidence)
            all_predictions = {
                CLASS_NAMES[i]: float(probabilities[i])
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
