import sys
import os
import shutil
import pandas as pd
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# Add project root to sys.path to allow importing from src
sys.path.append(os.getcwd())

from src.preprocessing.hybrid_pipeline import ImagePreprocessingPipeline

# Paths
RAW_IMAGES_DIR = "data/raw/images"
MASKS_DIR = "data/masks/lesion"
METADATA_PATH = "data/raw/metadata.csv"
PROCESSED_DIR = "data/processed"

def process_dataset():
    # 1. Load Metadata
    print("Loading metadata...")
    df = pd.read_csv(METADATA_PATH)
    
    # Filter out entries where image file doesn't exist
    valid_indices = []
    print("Validating image files...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        img_path = os.path.join(RAW_IMAGES_DIR, f"{row['image_id']}.jpg")
        if os.path.exists(img_path):
            valid_indices.append(idx)
    
    df = df.iloc[valid_indices]
    print(f"Found {len(df)} valid images.")

    # 2. Split Dataset (Stratified by 'dx')
    print("Splitting dataset...")
    # First split: Train (70%) vs Temp (30%)
    train_df, temp_df = train_test_split(
        df, test_size=0.3, stratify=df['dx'], random_state=42
    )
    # Second split: Val (15%) vs Test (15%) -> equal split of Temp
    val_df, test_df = train_test_split(
        temp_df, test_size=0.5, stratify=temp_df['dx'], random_state=42
    )
    
    print(f"Train size: {len(train_df)}")
    print(f"Val size: {len(val_df)}")
    print(f"Test size: {len(test_df)}")

    # 3. Process Images
    pipeline = ImagePreprocessingPipeline(target_size=(300, 300))
    
    splits = {
        "train": train_df,
        "val": val_df,
        "test": test_df
    }
    
    print("Processing images...")
    for split_name, split_df in splits.items():
        print(f"Processing {split_name} split...")
        for _, row in tqdm(split_df.iterrows(), total=len(split_df)):
            img_id = row['image_id']
            label = row['dx']
            
            # Paths
            img_path = os.path.join(RAW_IMAGES_DIR, f"{img_id}.jpg")
            mask_path = os.path.join(MASKS_DIR, f"{img_id}_segmentation.png")
            
            # Destination path for Final Processed Image
            dest_dir = os.path.join(PROCESSED_DIR, split_name, label)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, f"{img_id}.jpg")

            # Skip if already exists
            if os.path.exists(dest_path):
                continue

            try:
                # Load Image
                image = cv2.imread(img_path)
                if image is None:
                    print(f"Error reading image: {img_path}")
                    continue
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Load Mask (if exists)
                mask = None
                if os.path.exists(mask_path):
                    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                
                # Run Pipeline
                processed_img = pipeline.process(image, mask)
                
                # Save Final Processed Image
                save_img = cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR)
                if save_img.dtype != np.uint8:
                    save_img = (save_img * 255).astype(np.uint8)
                cv2.imwrite(dest_path, save_img)
                
            except Exception as e:
                print(f"Failed to process {img_id}: {e}")

    print("Dataset processing complete.")

if __name__ == "__main__":
    process_dataset()
