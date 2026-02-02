import os
import shutil
import random

# Configuration
SOURCE_IMG_DIR = "data/raw/images"
TARGET_DIR = "data/sample"
SAMPLE_SIZE = 10

def create_sample_data():
    """Create a sample dataset for GitHub"""
    print(f"Creating sample data in {TARGET_DIR}...")
    
    # Create target directory
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR)
    
    # Check source
    if not os.path.exists(SOURCE_IMG_DIR):
        print(f"❌ Source directory not found: {SOURCE_IMG_DIR}")
        return
    
    # Get list of images
    all_images = [f for f in os.listdir(SOURCE_IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not all_images:
        print("❌ No images found in source directory.")
        return
        
    # Select random sample
    sample_images = random.sample(all_images, min(SAMPLE_SIZE, len(all_images)))
    
    # Copy images
    print(f"Copying {len(sample_images)} images...")
    for img_name in sample_images:
        src = os.path.join(SOURCE_IMG_DIR, img_name)
        dst = os.path.join(TARGET_DIR, img_name)
        shutil.copy2(src, dst)
        print(f"  ✓ Copied: {img_name}")
        
    print(f"\n✅ Sample data created successfully with {len(sample_images)} images.")
    print(f"📁 Location: {TARGET_DIR}")

if __name__ == "__main__":
    create_sample_data()
