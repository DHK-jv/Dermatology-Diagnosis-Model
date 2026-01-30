"""
U-Net Model for Skin Lesion Segmentation
"""
import tensorflow as tf
from tensorflow.keras import layers, models
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.tf_config import setup_tensorflow
    setup_tensorflow()
except ImportError:
    print("⚠️  Warning: Could not import tf_config")
except Exception as e:
    print(f"⚠️  Warning: TensorFlow config error: {e}")


def conv_block(inputs, filters, kernel_size=3, activation='relu'):
    """
    Convolutional block: Conv2D -> BatchNorm -> Activation -> Conv2D -> BatchNorm -> Activation
    """
    x = layers.Conv2D(filters, kernel_size, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation(activation)(x)
    
    x = layers.Conv2D(filters, kernel_size, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation(activation)(x)
    
    return x


def encoder_block(inputs, filters):
    """
    Encoder block: ConvBlock -> MaxPooling
    Returns: output, skip_connection
    """
    x = conv_block(inputs, filters)
    p = layers.MaxPooling2D(pool_size=(2, 2))(x)
    return x, p


def decoder_block(inputs, skip_connection, filters):
    """
    Decoder block: UpSampling -> Concatenate -> ConvBlock
    """
    x = layers.Conv2DTranspose(filters, kernel_size=2, strides=2, padding='same')(inputs)
    x = layers.Concatenate()([x, skip_connection])
    x = conv_block(x, filters)
    return x


def build_unet(input_shape=(300, 300, 3), num_classes=1):
    """
    Builds a U-Net model for image segmentation.
    
    Args:
        input_shape (tuple): Input image shape (height, width, channels)
        num_classes (int): Number of segmentation classes (1 for binary, >1 for multi-class)
    
    Returns:
        tf.keras.Model: U-Net model
    """
    inputs = layers.Input(shape=input_shape)
    
    # Encoder Path
    s1, p1 = encoder_block(inputs, 64)      # 300x300 -> 150x150
    s2, p2 = encoder_block(p1, 128)          # 150x150 -> 75x75
    s3, p3 = encoder_block(p2, 256)          # 75x75 -> 37x37
    s4, p4 = encoder_block(p3, 512)          # 37x37 -> 18x18
    
    # Bottleneck
    b = conv_block(p4, 1024)                 # 18x18
    
    # Decoder Path
    d1 = decoder_block(b, s4, 512)           # 18x18 -> 37x37
    d2 = decoder_block(d1, s3, 256)          # 37x37 -> 75x75
    d3 = decoder_block(d2, s2, 128)          # 75x75 -> 150x150
    d4 = decoder_block(d3, s1, 64)           # 150x150 -> 300x300
    
    # Output Layer
    if num_classes == 1:
        # Binary segmentation
        outputs = layers.Conv2D(1, kernel_size=1, activation='sigmoid', padding='same')(d4)
    else:
        # Multi-class segmentation
        outputs = layers.Conv2D(num_classes, kernel_size=1, activation='softmax', padding='same')(d4)
    
    model = models.Model(inputs=inputs, outputs=outputs, name='UNet_Segmentation')
    
    return model


def dice_coefficient(y_true, y_pred, smooth=1e-6):
    """
    Dice Coefficient metric for segmentation
    """
    y_true_f = tf.keras.backend.flatten(y_true)
    y_pred_f = tf.keras.backend.flatten(y_pred)
    intersection = tf.keras.backend.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (tf.keras.backend.sum(y_true_f) + tf.keras.backend.sum(y_pred_f) + smooth)


def dice_loss(y_true, y_pred):
    """
    Dice Loss for segmentation
    """
    return 1 - dice_coefficient(y_true, y_pred)


def iou_score(y_true, y_pred, smooth=1e-6):
    """
    Intersection over Union (IoU) metric
    """
    y_true_f = tf.keras.backend.flatten(y_true)
    y_pred_f = tf.keras.backend.flatten(y_pred)
    intersection = tf.keras.backend.sum(y_true_f * y_pred_f)
    union = tf.keras.backend.sum(y_true_f) + tf.keras.backend.sum(y_pred_f) - intersection
    return (intersection + smooth) / (union + smooth)


if __name__ == "__main__":
    # Test build
    print("Building U-Net model...")
    model = build_unet(input_shape=(300, 300, 3), num_classes=1)
    
    # Compile with custom metrics
    model.compile(
        optimizer='adam',
        loss=dice_loss,
        metrics=[dice_coefficient, iou_score, 'binary_accuracy']
    )
    
    model.summary()
    
    print(f"\n✅ U-Net model created successfully!")
    print(f"   Input shape: (300, 300, 3)")
    print(f"   Output shape: (300, 300, 1)")
    print(f"   Total parameters: {model.count_params():,}")
