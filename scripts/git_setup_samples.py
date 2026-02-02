import os
import random
import subprocess
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(os.getcwd())
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_SIZE = 10

def get_image_files(directory):
    """Get list of image files in a directory"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    return [
        f for f in os.listdir(directory) 
        if os.path.isfile(os.path.join(directory, f)) 
        and os.path.splitext(f)[1].lower() in valid_extensions
    ]

def force_add_samples():
    """Find data directories and force add samples"""
    print(f"🔍 Scanning {DATA_DIR} for image directories...")
    
    total_added = 0
    dirs_processed = 0
    
    # Walk through data directory
    for root, dirs, files in os.walk(DATA_DIR):
        current_dir = Path(root)
        
        # Skip hidden directories
        if any(part.startswith('.') for part in current_dir.parts):
            continue
            
        images = get_image_files(current_dir)
        
        if images:
            # Randomly select samples
            sample_count = min(len(images), SAMPLE_SIZE)
            samples = random.sample(images, sample_count)
            
            print(f"\n📂 Processing: {current_dir.relative_to(PROJECT_ROOT)}")
            print(f"   Found {len(images)} images. Adding {sample_count} samples...")
            
            for img in samples:
                img_path = current_dir / img
                rel_path = img_path.relative_to(PROJECT_ROOT)
                
                # Git add -f
                try:
                    subprocess.run(
                        ["git", "add", "-f", str(rel_path)], 
                        check=True,
                        capture_output=True
                    )
                    total_added += 1
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ Failed to add {img}: {e}")
            
            dirs_processed += 1

    print(f"\n{'='*50}")
    print(f"✅ Completed!")
    print(f"   Directories processed: {dirs_processed}")
    print(f"   Total images added: {total_added}")
    print(f"{'='*50}")

if __name__ == "__main__":
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
    else:
        force_add_samples()
