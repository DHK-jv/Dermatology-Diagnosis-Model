import tensorflow as tf
from tensorflow.keras import layers, models, applications
import os
import sys

# Add parent directory to path to import tf_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.tf_config import setup_tensorflow
    # Setup TensorFlow with error handling
    setup_tensorflow()
except ImportError:
    print("⚠️  Warning: Could not import tf_config, using default TensorFlow config")
except Exception as e:
    print(f"⚠️  Warning: TensorFlow config error: {e}")

def build_model(num_classes, input_shape=(300, 300, 3), frozen_layers=None):
    """
    Builds an EfficientNet-B3 model for classification.
    
    Args:
        num_classes (int): Number of output classes.
        input_shape (tuple): Input image shape (height, width, channels). 
                             EfficientNet-B3 default is (300, 300, 3).
        frozen_layers (int, optional): Number of layers to freeze from the base model.
                                       If None, all base model layers are trainable.
    
    Returns:
        tf.keras.Model: Compiled EfficientNet-B3 model.
    """
    inputs = layers.Input(shape=input_shape)
    
    # Load EfficientNetB3 with ImageNet weights, excluding top layers
    base_model = applications.EfficientNetB3(
        include_top=False,
        weights="imagenet",
        input_tensor=inputs
    )
    
    # Freeze layers if specified
    if frozen_layers:
        # If frozen_layers is -1 or greater than total layers, freeze all
        if frozen_layers == -1 or frozen_layers >= len(base_model.layers):
            base_model.trainable = False
        else:
            # Freeze the first N layers
            for layer in base_model.layers[:frozen_layers]:
                layer.trainable = False
                
    # Rebuild top layers
    x = base_model.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name="EfficientNetB3_Dermatology")
    
    return model

if __name__ == "__main__":
    # Test build
    model = build_model(num_classes=7)
    model.summary()
