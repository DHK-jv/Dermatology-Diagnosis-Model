import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from preprocessing.hybrid_pipeline import ImagePreprocessingPipeline, HybridPreprocessingPipeline


def get_sample_image_from_raw():
    """
    Lấy ảnh gốc từ data/raw/images/
    """
    raw_dir = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'images')
    
    if not os.path.exists(raw_dir):
        print(f"⚠️  Raw images directory not found: {raw_dir}")
        return None
    
    # Lấy file ảnh đầu tiên
    image_files = [f for f in os.listdir(raw_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"⚠️  No images found in {raw_dir}")
        return None
    
    image_path = os.path.join(raw_dir, image_files[0])
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"⚠️  Failed to load image: {image_path}")
        return None
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image_rgb, image_files[0]


def get_sample_mask_from_processed():
    """
    Lấy mask từ data/masks/lesion/
    """
    mask_dir = os.path.join(os.path.dirname(__file__), 'data', 'masks', 'lesion')
    
    if not os.path.exists(mask_dir):
        print(f"⚠️  Masks directory not found: {mask_dir}")
        return None
    
    # Lấy file mask đầu tiên
    mask_files = [f for f in os.listdir(mask_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not mask_files:
        print(f"⚠️  No masks found in {mask_dir}")
        return None
    
    mask_path = os.path.join(mask_dir, mask_files[0])
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    if mask is None:
        print(f"⚠️  Failed to load mask: {mask_path}")
        return None
    
    return mask


def visualize_preprocessing_steps():
    """
    Hiển thị các bước xử lý ảnh
    """
    print("🔍 VISUALIZING IMAGE PREPROCESSING PIPELINE")
    
    # Lấy ảnh gốc
    print("📸 Loading original image...")
    result = get_sample_image_from_raw()
    if result is None:
        print("❌ Cannot load image. Exiting.")
        return
    
    original_image, filename = result
    print(f"✅ Loaded: {filename}")
    print(f"   Shape: {original_image.shape}, dtype: {original_image.dtype}")
    
    # Lấy mask
    print("\n🎭 Loading mask...")
    mask = get_sample_mask_from_processed()
    if mask is None:
        print("⚠️  Using empty mask")
        mask = np.zeros_like(original_image[:, :, 0])
    else:
        print(f"✅ Mask loaded. Shape: {mask.shape}")
    
    # Khởi tạo pipeline
    print("\n⚙️  Initializing preprocessing pipeline...")
    pipeline = ImagePreprocessingPipeline(target_size=(300, 300))
    
    # Lưu trữ các bước xử lý
    processing_steps = {
        '1. Original Image': original_image.copy(),
    }
    
    current_image = original_image.copy()
    
    # Bước 1: Segmentation (Crop)
    print("\n📍 Step 1: Segmentation & Cropping...")
    try:
        segmented = pipeline.lesion_segmentation_and_crop(current_image, mask)
        processing_steps['2. After Segmentation'] = segmented
        current_image = segmented
        print(f"   ✅ Segmented shape: {segmented.shape}")
    except Exception as e:
        print(f"   ⚠️  Segmentation failed: {e}")
    
    # Bước 2: Resize
    print("\n📏 Step 2: Resizing...")
    try:
        resized = pipeline.resize_image(current_image)
        processing_steps['3. After Resize'] = resized
        current_image = resized
        print(f"   ✅ Resized to: {resized.shape}")
    except Exception as e:
        print(f"   ⚠️  Resize failed: {e}")
    
    # Bước 3: Hair Removal
    print("\n✂️  Step 3: Hair Removal...")
    try:
        hair_removed = pipeline.hair_removal(current_image)
        processing_steps['4. After Hair Removal'] = hair_removed
        current_image = hair_removed
        print(f"   ✅ Hair removal completed")
    except Exception as e:
        print(f"   ⚠️  Hair removal failed: {e}")
    
    # Bước 4: Normalization
    print("\n🎨 Step 4: Normalization...")
    try:
        normalized = pipeline.pixel_normalization(current_image)
        processing_steps['5. Final (Normalized)'] = normalized
        current_image = normalized
        print(f"   ✅ Normalized to range: [{normalized.min():.3f}, {normalized.max():.3f}]")
    except Exception as e:
        print(f"   ⚠️  Normalization failed: {e}")
    
    # Visualize tất cả các bước
    print("📊 DISPLAYING PREPROCESSING STAGES")
    
    num_steps = len(processing_steps)
    fig, axes = plt.subplots(1, num_steps, figsize=(5*num_steps, 5))
    
    if num_steps == 1:
        axes = [axes]
    
    for idx, (step_name, step_image) in enumerate(processing_steps.items()):
        ax = axes[idx]
        
        # Xử lý ảnh để hiển thị
        if step_image.dtype == np.float32 or step_image.dtype == np.float64:
            display_image = np.clip(step_image * 255, 0, 255).astype(np.uint8)
        else:
            display_image = step_image
        
        # Nếu là ảnh grayscale, chuyển sang RGB để hiển thị
        if len(display_image.shape) == 2:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)
        elif display_image.shape[2] == 4:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGRA2RGB)
        
        ax.imshow(display_image)
        ax.set_title(step_name, fontsize=12, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout()
    
    # Lưu hình ảnh
    output_path = os.path.join(os.path.dirname(__file__), 'reports', 'figures', 'preprocessing_pipeline.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Visualization saved to: {output_path}")
    
    # Hiển thị
    plt.show()
    print("\n✅ All preprocessing steps completed successfully!")


def visualize_from_processed_dataset():
    """
    Hiển thị ảnh từ processed dataset để so sánh
    """
    print("\n" + "="*80)
    print("📁 SHOWING PROCESSED DATASET EXAMPLES")
    print("="*80 + "\n")
    
    processed_dir = os.path.join(os.path.dirname(__file__), 'data', 'processed', 'train')
    
    if not os.path.exists(processed_dir):
        print(f"⚠️  Processed dataset not found: {processed_dir}")
        return
    
    # Lấy ảnh mẫu từ các class khác nhau
    sample_images = {}
    
    for class_dir in sorted(os.listdir(processed_dir)):
        class_path = os.path.join(processed_dir, class_dir)
        if not os.path.isdir(class_path):
            continue
        
        image_files = [f for f in os.listdir(class_path) if f.endswith(('.jpg', '.png'))]
        
        if image_files:
            img_path = os.path.join(class_path, image_files[0])
            img = cv2.imread(img_path)
            if img is not None:
                sample_images[class_dir] = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    if not sample_images:
        print("⚠️  No processed images found")
        return
    
    # Hiển thị
    num_classes = len(sample_images)
    fig, axes = plt.subplots(1, num_classes, figsize=(5*num_classes, 5))
    
    if num_classes == 1:
        axes = [axes]
    
    for idx, (class_name, img) in enumerate(sample_images.items()):
        ax = axes[idx]
        ax.imshow(img)
        ax.set_title(f"Class: {class_name}", fontsize=12, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout()
    
    # Lưu hình ảnh
    output_path = os.path.join(os.path.dirname(__file__), 'reports', 'figures', 'processed_dataset_samples.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Dataset samples saved to: {output_path}")
    
    plt.show()


if __name__ == '__main__':
    try:
        # Chạy visualization
        visualize_preprocessing_steps()
        
        # Hiển thị processed dataset
        print("\n")
        visualize_from_processed_dataset()
        
        print("\n" + "="*80)
        print("✨ VISUALIZATION COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()
