import os
import shutil
import pandas as pd
import glob
from tqdm import tqdm

# Configuration
ISIC_INPUT_DIR = "/home/khangjv/WorkSpace/MedAI_Dermatology/ISIC_2019_Training_Input"
RAW_IMAGES_DIR = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/raw/images"
PROCESSED_DIR = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/processed_isic2019"
OUTPUT_METADATA_PATH = "/home/khangjv/WorkSpace/MedAI_Dermatology/data/raw/isic_2019_ground_truth.csv"

LABEL_COLS = ['MEL', 'NV', 'BCC', 'AK', 'BKL', 'DF', 'VASC', 'SCC']
FOLDER_TO_LABEL = {
    'mel': 'MEL',
    'nv': 'NV',
    'bcc': 'BCC',
    'akiec': 'AK',
    'bkl': 'BKL',
    'df': 'DF',
    'vasc': 'VASC',
    'scc': 'SCC'
}

def merge_images():
    print("🚀 Starting Image Merge...")
    os.makedirs(RAW_IMAGES_DIR, exist_ok=True)
    
    # Get list of files in ISIC input
    files = glob.glob(os.path.join(ISIC_INPUT_DIR, "*"))
    print(f"found {len(files)} files in {ISIC_INPUT_DIR}")
    
    # Copy files
    print(f"Copying files to {RAW_IMAGES_DIR}...")
    for src_path in tqdm(files):
        filename = os.path.basename(src_path)
        dst_path = os.path.join(RAW_IMAGES_DIR, filename)
        
        if os.path.isfile(src_path):
             shutil.copy2(src_path, dst_path)
             
    print("✅ Image join completed.")

def reconstruct_metadata():
    print("🔄 Reconstructing Clean Metadata from Processed Data...")
    
    records = []
    
    # Iterate through structured folders (train, val, test)
    for split in ['train', 'val', 'test']:
        split_dir = os.path.join(PROCESSED_DIR, split)
        if not os.path.exists(split_dir):
            print(f"Skipping {split} (not found)")
            continue
            
        for class_dir in os.listdir(split_dir):
            label_key = class_dir.lower()
            if label_key not in FOLDER_TO_LABEL:
                continue
                
            col_name = FOLDER_TO_LABEL[label_key]
            full_class_dir = os.path.join(split_dir, class_dir)
            
            if not os.path.isdir(full_class_dir):
                continue

            for img_file in os.listdir(full_class_dir):
                if not img_file.endswith('.jpg'):
                    continue
                
                image_id = os.path.splitext(img_file)[0]
                
                # Create one-hot record
                record = {'image': image_id}
                for col in LABEL_COLS:
                    record[col] = 1.0 if col == col_name else 0.0
                
                records.append(record)
                
    df = pd.DataFrame(records)
    
    if len(df) > 0:
        # De-duplicate
        df = df.drop_duplicates(subset=['image'])
        
        print(f"📊 Reconstructed {len(df)} labels.")
        
        # Save to CSV
        df.to_csv(OUTPUT_METADATA_PATH, index=False)
        print(f"💾 Saved metadata to {OUTPUT_METADATA_PATH}")
    else:
        print("⚠️ No labels found in processed directory!")

if __name__ == "__main__":
    merge_images()
    reconstruct_metadata()
