
import os
import cv2
import pandas as pd
import numpy as np
from tqdm import tqdm
import shutil
from sklearn.model_selection import train_test_split

# Configuration
RAW_IMAGES_DIR = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/raw/images"
RAW_CSV_PATH = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/raw/isic_2019_ground_truth.csv"
OUTPUT_DIR = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/processed_isic2019"
TARGET_SIZE = (300, 300)

# Label Mapping
LABEL_MAP = {
    'MEL': 'mel',       # Melanoma
    'NV': 'nv',         # Melanocytic nevi
    'BCC': 'bcc',       # Basal cell carcinoma
    'AK': 'akiec',      # Actinic keratosis
    'BKL': 'bkl',       # Benign keratosis-like lesions
    'DF': 'df',         # Dermatofibroma
    'VASC': 'vasc',     # Vascular lesions
    'SCC': 'scc',       # Squamous cell carcinoma
}

def get_label(row):
    for col, target_name in LABEL_MAP.items():
        if row[col] == 1.0:
            return target_name
    return None

def process_and_save(df, split_name):
    """
    Process specific split dataframe
    """
    split_dir = os.path.join(OUTPUT_DIR, split_name)
    os.makedirs(split_dir, exist_ok=True)
    
    # Create class dirs
    for label in LABEL_MAP.values():
        os.makedirs(os.path.join(split_dir, label), exist_ok=True)
        
    print(f"🖼️  Processing {split_name} set ({len(df)} images)...")
    
    success_count = 0
    
    for index, row in tqdm(df.iterrows(), total=len(df)):
        image_id = row['image']
        label = row['target_label']
        
        # Image Paths
        src_path = os.path.join(RAW_IMAGES_DIR, f"{image_id}.jpg")
        if not os.path.exists(src_path):
            src_path_down = os.path.join(RAW_IMAGES_DIR, f"{image_id}_downsampled.jpg")
            if os.path.exists(src_path_down):
                src_path = src_path_down
            else:
                continue
                
        # Load and Resize
        try:
            img = cv2.imread(src_path)
            if img is None:
                continue
            
            img_resized = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)
            
            # Save to class folder
            dst_filename = f"{image_id}.jpg"
            dst_path = os.path.join(split_dir, label, dst_filename)
            cv2.imwrite(dst_path, img_resized)
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {image_id}: {e}")
            continue
            
    print(f"✅ {split_name} completed: {success_count}/{len(df)}")


def preprocess_isic_data():
    """
    Reads ISIC 2019 GT, splits into Train/Val/Test, resizes, and organizes.
    """
    print(f"🚀 Starting ISIC 2019 Preprocessing & Splitting...")
    
    # 1. Setup Directories - CLEAN START
    if os.path.exists(OUTPUT_DIR):
        print(f"⚠️  Output directory exists. Cleaning up: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. Read Meta CSV
    print(f"📖 Reading Ground Truth CSV: {RAW_CSV_PATH}")
    df = pd.read_csv(RAW_CSV_PATH)
    
    # Filter UNK
    if 'UNK' in df.columns and df['UNK'].sum() > 0:
        df = df[df['UNK'] != 1.0]

    # Assign labels
    df['target_label'] = df.apply(get_label, axis=1)
    df = df.dropna(subset=['target_label']) # Drop unmapped
    
    print(f"📊 Total valid samples: {len(df)}")
    
    # 3. Stratified Split
    # Train: 80%, Temp: 20% -> Val: 10%, Test: 10%
    train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df['target_label'], random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df['target_label'], random_state=42)
    
    print(f"📦 Split Sizes:")
    print(f"   Train: {len(train_df)}")
    print(f"   Val:   {len(val_df)}")
    print(f"   Test:  {len(test_df)}")
    
    # 4. Process Splits
    process_and_save(train_df, 'train')
    process_and_save(val_df, 'val')
    process_and_save(test_df, 'test')
    
    # 5. Zip the result for easy upload
    print(f"📦 Zipping processed data...")
    shutil.make_archive("processed_isic_2019", 'zip', OUTPUT_DIR)
    print(f"✅ Zip created: processed_isic_2019.zip")
    
    print(f"✅ All Done!")

if __name__ == "__main__":
    preprocess_isic_data()
