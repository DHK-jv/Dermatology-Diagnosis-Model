import os
import re
import shutil
import cv2
import polars as pl
import numpy as np
from collections import Counter
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import hashlib
import imagehash
import sys
import json
import csv
from concurrent.futures import ThreadPoolExecutor
from sklearn.model_selection import GroupShuffleSplit

# Import Hybrid Pipeline
# Add project root to path for consistent imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from preprocessing.hybrid_pipeline import HybridPreprocessingPipeline

# --- CONFIG ---
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
IMG_SIZE = (380, 380)
MIN_VAL_PER_CLASS = 50  # Minimum validation samples per class
VAL_RATIO = 0.15  # Target validation ratio

# --- CLASS MAPPING (24 Classes) ---
CLASS_MAPPING_24 = {
    'MEL': 'melanoma',
    'NV': 'melanocytic_nevus',
    'BCC': 'basal_cell_carcinoma',
    'AK': 'actinic_keratosis',
    'SCC': 'squamous_cell_carcinoma',
    'BKL': 'seborrheic_keratosis',
    'DF': 'dermatofibroma',
    'VASC': 'vascular_lesion',
    'NEV': 'melanocytic_nevus',
    'ACK': 'actinic_keratosis',
    'SEK': 'seborrheic_keratosis',
}

PAD_TO_CANONICAL = {
    'MEL': 'melanoma',
    'NEV': 'melanocytic_nevus',
    'BCC': 'basal_cell_carcinoma',
    'ACK': 'actinic_keratosis',
    'SCC': 'squamous_cell_carcinoma',
    'SEK': 'seborrheic_keratosis'
}

ISIC_TO_CANONICAL = {
    'MEL': 'melanoma',
    'NV': 'melanocytic_nevus',
    'BCC': 'basal_cell_carcinoma',
    'AK': 'actinic_keratosis',
    'SCC': 'squamous_cell_carcinoma',
    'BKL': 'seborrheic_keratosis',
    'DF': 'dermatofibroma',
    'VASC': 'vascular_lesion'
}

# FIXED: Class mapping to match 24-class list
DERMNET_MAPPING = {
    "acne": "acne_rosacea",
    "rosacea": "acne_rosacea",
    "bullous": "bullous_disease_pemphigus",
    "pemphigus": "bullous_disease_pemphigus",
    "cellulitis": "cellulitis_impetigo",
    "impetigo": "cellulitis_impetigo",
    "eczema": "eczema_atopic_dermatitis",
    "atopic": "eczema_atopic_dermatitis",
    "exanthems": "exanthems_drug_eruptions",
    "drug": "exanthems_drug_eruptions",
    "hair": "alopecia_hair_loss",
    "alopecia": "alopecia_hair_loss",
    "viral": "viral_infections",
    "warts": "viral_infections",
    "molluscum": "viral_infections",
    "herpes": "viral_infections",
    "pigmentation": "pigmentation_disorders",
    "pigment": "pigmentation_disorders",
    "lupus": "lupus_connective_tissue",
    "connective": "lupus_connective_tissue",
    "nail": "fungal_infections",

    "fungus": "fungal_infections",
    "tinea": "fungal_infections",
    "psoriasis": "psoriasis_lichen_planus",
    "lichen": "psoriasis_lichen_planus",
    "scabies": "infestations_bites",
    "systemic": "systemic_disease",
    "urticaria": "urticaria_hives",
    "hives": "urticaria_hives",
    "vasculitis": "vasculitis",
    "contact": "contact_dermatitis",
    "poison": "contact_dermatitis",
    # SKIPS
    "melanoma": None, "nevi": None, "moles": None, "basal": None, "squamous": None, 
    "actinic": None, "seborrheic": None, "vascular": None
}

# --- QUALITY CONTROL ---
def validate_image_quality(img_path):
    """Check image quality before processing"""
    try:
        # 1. Can open and verify
        img = Image.open(img_path)
        img.verify()
        img = Image.open(img_path)  # Reopen after verify
        
        # 2. Size check
        if min(img.size) < 100:
            return False, "Too small"
        
        # 3. Aspect ratio
        ratio = max(img.size) / min(img.size)
        if ratio > 3:
            return False, "Extreme aspect ratio"
        
        # 4. Brightness
        arr = np.array(img)
        if len(arr.shape) < 2:
            return False, "Invalid image"
        
        mean_brightness = arr.mean()
        if mean_brightness < 20 or mean_brightness > 235:
            return False, "Too dark/bright"
        
        # 5. Color channels
        if len(arr.shape) != 3 or arr.shape[2] != 3:
            return False, "Not RGB"
        
        # 6. File size
        if img_path.stat().st_size < 5000:
            return False, "File too small (corrupted?)"
        
        return True, "OK"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_image_hash(filepath):
    """Calculate Perceptual Hash of image to detect resized/compressed duplicates"""
    try:
        # Load and lightly resize before hashing to avoid semantic duplicates from YOLO segmentation and high res images
        img = Image.open(filepath).convert('RGB')
        img.thumbnail((256, 256), Image.Resampling.LANCZOS)
        return str(imagehash.phash(img))
    except Exception:
        # Fallback to MD5 if Image open fails for hashing but passed verify
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

def resolve_dermnet_label(folder_name):
    name_check = folder_name.lower()
    
    # 1. Check skips
    for k, v in DERMNET_MAPPING.items():
        if v is None and re.search(rf"\b{k}\b", name_check):
            return None
            
    # 2. Check mappings
    keys = sorted([k for k, v in DERMNET_MAPPING.items() if v is not None], key=len, reverse=True)
    for k in keys:
        if re.search(rf"\b{k}\b", name_check):
            return DERMNET_MAPPING[k]
            
    return None
            


# --- PATIENT METADATA LOADING ---
def load_patient_metadata():
    """Load patient_id mappings from ISIC and PAD metadata"""
    patient_map = {}  # image_name -> patient_id
    
    print("📋 Loading patient metadata...")
    
    # ISIC 2019 - Check for metadata file
    isic_meta = RAW_DATA_DIR / "isic_2019" / "ISIC_2019_Training_Metadata.csv"
    if isic_meta.exists():
        print(f"  Found ISIC metadata: {isic_meta}")
        df_meta = pl.read_csv(isic_meta)
        for row in df_meta.iter_rows(named=True):
            img_name = row.get('image')
            # Try different column names
            patient_id = (row.get('patient_id') or 
                         row.get('lesion_id') or 
                         row.get('patient') or
                         row.get('lesion'))
            if img_name and patient_id:
                patient_map[img_name] = str(patient_id)
                patient_map[f"{img_name}.jpg"] = str(patient_id)
        print(f"    Loaded {len(patient_map)} ISIC patient mappings")
    else:
        print(f"  ISIC metadata not found at {isic_meta}")
    
    # PAD-UFES-20
    pad_csv = RAW_DATA_DIR / "pad_ufes_20" / "metadata.csv"
    if pad_csv.exists():
        print(f"  Found PAD metadata: {pad_csv}")
        df_pad = pl.read_csv(pad_csv, infer_schema_length=50000)
        pad_count = 0
        for row in df_pad.iter_rows(named=True):
            img_id = row.get('img_id')
            patient_id = row.get('patient_id')
            if img_id and patient_id:
                patient_map[img_id] = str(patient_id)
                patient_map[f"{img_id}.png"] = str(patient_id)
                pad_count += 1
        print(f"    Loaded {pad_count} PAD patient mappings")
    else:
        print(f"  PAD metadata not found at {pad_csv}")
    
    print(f"✅ Total patient mappings: {len(patient_map)}")
    return patient_map

# --- COLLECT IMAGES BY CLASS ---
def collect_images_by_class():
    """Collect all images grouped by class with patient info"""
    patient_map = load_patient_metadata()
    
    class_data = {}  # class_name -> [(img_path, patient_id, hash), ...]
    seen_hashes = set()
    quality_failed = 0
    duplicates = 0
    
    print("\n🔍 Scanning raw images...")
    file_map = {}
    all_files = []
    
    for f in sorted(list(RAW_DATA_DIR.rglob("*"))):
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            all_files.append(f)
            file_map[f.name] = f
    
    print(f"  Found {len(all_files)} total image files")
    
    # --- ISIC 2019 ---
    print("\n🔄 Processing ISIC 2019...")
    isic_csv = RAW_DATA_DIR / "isic_2019" / "ISIC_2019_Training_GroundTruth.csv"
    if isic_csv.exists():
        df = pl.read_csv(isic_csv)
        df = df.sample(fraction=1.0, shuffle=True, seed=42)
        
        for row in tqdm(df.iter_rows(named=True), total=len(df), desc="ISIC"):
            img_name = row['image'] + ".jpg"
            if img_name not in file_map:
                continue
            
            src_path = file_map[img_name]
            
            # Quality check
            is_valid, reason = validate_image_quality(src_path)
            if not is_valid:
                quality_failed += 1
                log_path = ROOT_DIR / "data" / "quality_failed_logs.csv"
                with open(log_path, "a", newline="", encoding="utf-8") as f_log:
                    writer = csv.writer(f_log)
                    writer.writerow([src_path, "ISIC", reason])
                continue
            
            # Deduplication
            file_hash = get_image_hash(src_path)
            if file_hash in seen_hashes:
                duplicates += 1
                continue
            seen_hashes.add(file_hash)
            
            # Get label
            label = None
            for col, target in ISIC_TO_CANONICAL.items():
                if row.get(col) == 1.0:
                    label = target
                    break
            if not label:
                continue
            
            # Get patient_id
            patient_id = patient_map.get(row['image']) or patient_map.get(img_name)
            
            class_data.setdefault(label, []).append((src_path, patient_id, file_hash, "ISIC"))
    
    # --- PAD-UFES-20 ---
    print("\n🔄 Processing PAD-UFES-20...")
    pad_csv = RAW_DATA_DIR / "pad_ufes_20" / "metadata.csv"
    if pad_csv.exists():
        df_pad = pl.read_csv(pad_csv, infer_schema_length=50000)
        for row in tqdm(df_pad.iter_rows(named=True), total=len(df_pad), desc="PAD"):
            img_id = row['img_id']
            
            if img_id in file_map:
                src_path = file_map[img_id]
            elif f"{img_id}.png" in file_map:
                src_path = file_map[f"{img_id}.png"]
            else:
                continue
            
            # Quality check
            is_valid, reason = validate_image_quality(src_path)
            if not is_valid:
                quality_failed += 1
                log_path = ROOT_DIR / "data" / "quality_failed_logs.csv"
                with open(log_path, "a", newline="", encoding="utf-8") as f_log:
                    writer = csv.writer(f_log)
                    writer.writerow([src_path, "PAD-UFES-20", reason])
                continue
            
            # Deduplication
            file_hash = get_image_hash(src_path)
            if file_hash in seen_hashes:
                duplicates += 1
                continue
            seen_hashes.add(file_hash)
            
            diag = row['diagnostic']
            if diag in PAD_TO_CANONICAL:
                label = PAD_TO_CANONICAL[diag]
                patient_id = patient_map.get(img_id) or patient_map.get(f"{img_id}.png")
                class_data.setdefault(label, []).append((src_path, patient_id, file_hash, "PAD"))
    
    # --- DermNet ---
    print("\n🔄 Processing DermNet & Others...")
    dermnet_root = RAW_DATA_DIR / "dermnet"
    if dermnet_root.exists():
        for f in tqdm(list(dermnet_root.rglob("*")), desc="DermNet"):
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                # Quality check
                is_valid, reason = validate_image_quality(f)
                if not is_valid:
                    quality_failed += 1
                    log_path = ROOT_DIR / "data" / "quality_failed_logs.csv"
                    with open(log_path, "a", newline="", encoding="utf-8") as f_log:
                        writer = csv.writer(f_log)
                        writer.writerow([f, "DermNet", reason])
                    continue
                
                # Deduplication
                file_hash = get_image_hash(f)
                if file_hash in seen_hashes:
                    duplicates += 1
                    continue
                seen_hashes.add(file_hash)
                
                parent_name = f.parent.name
                label = resolve_dermnet_label(parent_name)
                
                if label:
                    # DermNet has no patient_id
                    class_data.setdefault(label, []).append((f, None, file_hash, "DERMNET"))
    
    print(f"\n📊 Collection complete:")
    print(f"  Quality failed: {quality_failed}")
    print(f"  Duplicates removed: {duplicates}")
    print(f"  Classes found: {len(class_data)}")
    
    return class_data

# --- PATIENT-BASED SPLIT ---
def create_stratified_patient_split(class_data):
    """Split by patient and domain source, ensuring min validation samples per class"""
    rng = np.random.default_rng(42)
    print(f"\\n🔀 Creating patient-based split (min {MIN_VAL_PER_CLASS} val/class)...")
    
    train_samples = []
    val_samples = []
    
    for class_name, samples in class_data.items():
        print(f"\\n  {class_name}: {len(samples)} images")
        
        # Group by patient
        patient_groups = {}
        no_patient = {}  # source -> list of samples
        
        for img_path, patient_id, file_hash, source in samples:
            if patient_id:
                patient_groups.setdefault(patient_id, []).append((img_path, file_hash, source))
            else:
                no_patient.setdefault(source, []).append((img_path, file_hash, source))
        
        print(f"    With patient_id: {sum(len(v) for v in patient_groups.values())} images ({len(patient_groups)} patients)")
        print(f"    Without patient_id: {sum(len(v) for v in no_patient.values())} images")
        
        total = len(samples)
        
        # Split patients (not images)
        if len(patient_groups) > 0:
            patients = list(patient_groups.keys())
            patient_samples = [patient_groups[p] for p in patients]
            
            # Group shuffle split
            gss = GroupShuffleSplit(n_splits=1, test_size=VAL_RATIO, random_state=42)
            
            X = np.arange(len(patient_samples))
            y = [0] * len(patient_samples)
            groups = patients
            
            train_idx, val_idx = next(gss.split(X, y, groups))
            
            for idx in train_idx:
                for img_path, file_hash, source in patient_samples[idx]:
                    train_samples.append((img_path, class_name, file_hash, source, "train"))
            
            for idx in val_idx:
                for img_path, file_hash, source in patient_samples[idx]:
                    val_samples.append((img_path, class_name, file_hash, source, "val"))
        
        # Handle images without patient_id (DermNet) with domain-aware split
        for source, source_samples in no_patient.items():
            rng.shuffle(source_samples)
            
            n_val_source = int(len(source_samples) * VAL_RATIO)
            
            for img_path, file_hash, src in source_samples[:n_val_source]:
                val_samples.append((img_path, class_name, file_hash, src, "val"))
            for img_path, file_hash, src in source_samples[n_val_source:]:
                train_samples.append((img_path, class_name, file_hash, src, "train"))
        
        # Balance validation minimums (only move from train to val if needed)
        current_val = [s for s in val_samples if s[1] == class_name]
        current_train = [s for s in train_samples if s[1] == class_name]
        
        # Upper bound constraint (LỖI #5)
        n_val_target = min(
            max(MIN_VAL_PER_CLASS, int(total * VAL_RATIO)),
            int(total * 0.25)
        )
        
        if len(current_val) < n_val_target and len(current_train) > 0:
            needed = n_val_target - len(current_val)
            move_count = min(needed, len(current_train))
            
            # Move `move_count` items from train to val
            to_move = current_train[:move_count]
            
            # Remove from train, add to val
            for item in to_move:
                train_samples.remove(item)
                val_samples.append((*item[:-1], "val"))
                
        final_val_count = len([s for s in val_samples if s[1] == class_name])
        final_train_count = len([s for s in train_samples if s[1] == class_name])
        print(f"    → Train: {final_train_count}, Val: {final_val_count}")
    
    print(f"\n✅ Split complete:")
    print(f"  Total train: {len(train_samples)}")
    print(f"    Train Domain Dist: {dict(Counter([s[3] for s in train_samples]))}")
    print(f"  Total val: {len(val_samples)}")
    print(f"    Val Domain Dist: {dict(Counter([s[3] for s in val_samples]))}")
    
    return train_samples, val_samples

def process_single_image(args):
    img_path, label, file_hash, source, split, pipeline = args
    try:
        # Read
        img = cv2.imread(str(img_path))
        if img is None:
            return False
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Process
        processed_img = pipeline.process(img, verbose=False)
        
        # Convert to uint8
        if processed_img.max() <= 1.05:
            processed_img = (processed_img * 255).astype(np.uint8)
        else:
            processed_img = processed_img.astype(np.uint8)
        
        # Save
        out_name = f"{label}_{img_path.stem}.jpg"
        target_path = PROCESSED_DATA_DIR / split / label / out_name
        os.makedirs(target_path.parent, exist_ok=True)
        
        Image.fromarray(processed_img).save(target_path, quality=95)
        return True
    except Exception as e:
        return False

# --- PROCESS AND SAVE ---
def process_and_save_samples(samples, pipeline):
    """Process and save images to train/val folders using Multiprocessing"""
    print(f"\\n🔄 Processing {len(samples)} images...")
    
    processed = 0
    failed = 0
    
    # Pack arguments including the pre-determined 'split'
    tasks = [(p, l, h, src, spl, pipeline) for p, l, h, src, spl in samples]
    
    # Run Sequentially because YOLOv8 Inference is not Thread-Safe
    for task in tqdm(tasks, desc="Processing sequentially"):
        if process_single_image(task):
            processed += 1
        else:
            failed += 1
        
    print(f"✅ Processed: {processed}, Failed: {failed}")

def print_stats():
    """Print final dataset statistics"""
    print("\n" + "="*60)
    print("📊 FINAL DATASET STATISTICS")
    print("="*60)
    
    for split in ['train', 'val']:
        split_dir = PROCESSED_DATA_DIR / split
        if not split_dir.exists():
            continue
        
        print(f"\n{split.upper()}:")
        total = 0
        for class_dir in sorted(split_dir.iterdir()):
            if class_dir.is_dir():
                count = len(list(class_dir.glob("*")))
                print(f"  {class_dir.name:30s}: {count:5d} images")
                total += count
        print(f"  {'TOTAL':30s}: {total:5d} images")
    
    # Calculate Class Weights based on Train split
    train_dir = PROCESSED_DATA_DIR / 'train'
    if train_dir.exists():
        class_counts = {}
        total_train = 0
        for class_dir in sorted(train_dir.iterdir()):
            if class_dir.is_dir():
                count = len(list(class_dir.glob("*")))
                class_counts[class_dir.name] = count
                total_train += count
                
        if total_train > 0:
            num_classes = len(class_counts)
            class_weights = {}
            for cls_name, count in class_counts.items():
                if count > 0:
                    weight = total_train / (num_classes * count)
                    class_weights[cls_name] = weight
            
            weights_path = ROOT_DIR / "preprocessing" / "class_weights.json"
            with open(weights_path, "w") as f:
                json.dump(class_weights, f, indent=4)
            print(f"\n✅ Saved class weights to {weights_path}")

    print("\n" + "="*60)

# --- MAIN ---
def main():
    print("🚀 Dataset Regeneration with Quality Fixes")
    print("="*60)
    
    # Initialize quality failures log
    log_path = ROOT_DIR / "data" / "quality_failed_logs.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f_log:
        writer = csv.writer(f_log)
        writer.writerow(["ImagePath", "DatasetSource", "Reason"])
        
    # Wipe and recreate
    if PROCESSED_DATA_DIR.exists():
        print(f"🗑️  Wiping {PROCESSED_DATA_DIR}...")
        shutil.rmtree(PROCESSED_DATA_DIR)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # Initialize pipeline
    pipeline = HybridPreprocessingPipeline(
        mode='auto',
        target_size=IMG_SIZE,
        yolo_model_path=str(ROOT_DIR / "backend" / "ml_models" / "yolov8n-seg.pt")
    )
    
    # Collect images
    class_data = collect_images_by_class()
    
    # Create patient-based split
    global train_samples, val_samples
    train_samples, val_samples = create_stratified_patient_split(class_data)
    
    # Process and save
    all_samples = train_samples + val_samples
    process_and_save_samples(all_samples, pipeline)
    
    # Print stats
    print_stats()
    
    print("\n✅ Dataset regeneration complete!")

if __name__ == "__main__":
    main()
