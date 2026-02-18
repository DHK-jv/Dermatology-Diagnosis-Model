# 🏥 MedAI Dermatology - AI Skin Disease Diagnosis

> **Author:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Deep Learning-based Skin Disease Classification System**

---

## 📊 Overview

An AI-powered dermatology diagnosis system using advanced deep learning and medical image processing. The system integrates professional preprocessing pipelines and state-of-the-art neural networks to assist in skin disease diagnosis.

**Key Achievements:**
- ✅ **Dataset:** ~41k images (DermNet NZ + ISIC 2019 + PAD-UFES-20)
- ✅ **Preprocessing:** Automated pipeline (YOLOv8 Segmentation + Hair Removal + Quality Control)
- ✅ **Model:** EfficientNet-B4 V2 (73.9% validation accuracy, F1 0.670)
- ✅ **System:** Full-stack application with FastAPI backend and modern web frontend
- ✅ **Classes:** 24 dermatological conditions with Vietnamese translations

---

## 🚀 Quick Start

```bash
git clone https://github.com/DHK-jv/Dermatology-Diagnosis-Model.git
cd Dermatology-Diagnosis-Model
python run.py
```

System will auto-start at: http://localhost:8080

---

## 🏥 Supported Diseases (24 Classes)

| Vietnamese | English | Risk |
|-----------|---------|------|
| Mụn trứng cá & Rosacea | Acne Rosacea | Low |
| Dày sừng quang hóa | Actinic Keratosis | Medium ⚠️ |
| Rụng tóc | Alopecia Hair Loss | Low |
| **Ung thư tế bào đáy** | **Basal Cell Carcinoma** | **High ⚠️** |
| Bệnh bóng nước | Bullous Disease | Medium |
| Viêm mô tế bào | Cellulitis Impetigo | Medium |
| Viêm da tiếp xúc | Contact Dermatitis | Low |
| U xơ da lành tính | Dermatofibroma | Low |
| Chàm & Viêm da cơ địa | Eczema Atopic Dermatitis | Low |
| Phát ban do thuốc | Drug Eruptions | Medium |
| Nấm da | Fungal Infections | Low |
| Côn trùng cắn | Infestations Bites | Low |
| Lupus & Bệnh mô liên kết | Lupus | High ⚠️ |
| Nốt ruồi lành tính | Melanocytic Nevus | Low |
| **Ung thư hắc tố** | **Melanoma** | **Critical 🚨** |
| Rối loạn sắc tố | Pigmentation Disorders | Low |
| Vảy nến | Psoriasis Lichen Planus | Medium |
| Dày sừng tiết bã | Seborrheic Keratosis | Low |
| **Ung thư tế bào vảy** | **Squamous Cell Carcinoma** | **High ⚠️** |
| Biểu hiện da bệnh nội khoa | Systemic Disease | High |
| Mề đay | Urticaria Hives | Low |
| Tổn thương mạch máu | Vascular Lesion | Medium |
| Viêm mạch máu | Vasculitis | High |
| Nhiễm trùng virus | Viral Infections | Low |

---

## 📁 Project Structure

```
MedAI_Dermatology/
│
├── 📂 backend/                      # Backend System (FastAPI)
│   ├── app/
│   │   ├── models/                  # Pydantic schemas
│   │   ├── services/                # Business logic
│   │   │   ├── inference.py         # AI model inference
│   │   │   ├── preprocessing.py     # Image preprocessing
│   │   │   └── storage.py           # Data persistence
│   │   ├── utils/
│   │   │   └── constants.py         # Disease mappings & configs
│   │   ├── config.py                # System configuration
│   │   └── main.py                  # API endpoints
│   │
│   ├── ml_models/                   # AI Models
│   │   ├── efficientnet_b4_derma_v2.pth    # Main classifier (V2)
│   │   └── yolov8n-seg.pt           # Segmentation model
│   │
│   └── uploads/                     # Temporary upload storage
│
├── 📂 frontend/                     # Web Interface
│   ├── assets/                      # Images, logos
│   ├── css/                         # Stylesheets
│   ├── js/                          # JavaScript
│   │   ├── app.js                   # Main app logic
│   │   ├── api.js                   # API client
│   │   └── diagnose.js              # Diagnosis flow
│   ├── pages/                       # HTML pages
│   │   ├── diagnose.html            # Diagnosis page
│   │   ├── history.html             # History page
│   │   └── result.html              # Results page
│   └── index.html                   # Landing page
│
├── 📂 preprocessing/                # Image Preprocessing
│   ├── hybrid_pipeline.py           # Main preprocessing pipeline
│   └── yolo_segmentor.py            # YOLO segmentation wrapper
│
├── 📂 research/                     # Research & Training
│   ├── notebooks/
│   │   ├── kaggle-train.ipynb       # Main training notebook
│   │   ├── 01_eda_data.ipynb        # Data analysis
│   │   └── 02_processed_data_check.ipynb
│   └── reports/                     # Training reports
│
├── 📂 data/                         # Dataset
│   ├── raw/                         # Raw images
│   │   ├── dermnet/                 # DermNet NZ
│   │   ├── isic_2019/               # ISIC 2019
│   │   └── pad_ufes/                # PAD-UFES-20
│   └── processed/                   # Processed dataset
│       ├── train/                   # Training set (~33k images)
│       └── val/                     # Validation set (~8k images)
│
├── 📄 prepare_dataset_local.py      # Dataset preparation script
├── 📄 run.py                        # System launcher
├── 📄 requirements.txt              # Python dependencies
└── 📄 README.md                     # This file
```

---

## ⚙️ Preprocessing Pipeline

The system uses a sophisticated preprocessing pipeline:

```
Raw Image (any size)
    ↓
1. YOLO Segmentation (YOLOv8n-seg)
   - Detect and isolate skin lesion
   - Remove background
    ↓
2. Hair Removal (DullRazor Algorithm)
   - Remove hair artifacts
   - Reduce noise
    ↓
3. Quality Control
   - Check image quality
   - Validate dimensions
    ↓
4. Resize & Normalize
   - Resize to 380x380
   - Normalize to [0-1]
    ↓
5. AI Inference (EfficientNet-B4)
   - Extract features
   - Classify into 24 classes
    ↓
Output: Disease prediction + confidence
```

---

## 🔬 Training Details

### **Dataset Composition**

| Source | Images | Classes | Usage |
|--------|--------|---------|-------|
| DermNet NZ | ~23k | 23 | Primary training |
| ISIC 2019 | ~25k | 8 | Melanoma focus |
| PAD-UFES-20 | ~2k | 6 | Patient metadata |
| **Total** | **~41k** | **24 (merged)** | **Combined** |

### **Data Split**

- **Training**: 80% (~33k images)
- **Validation**: 20% (~8k images)
- **Split Method**: Patient-based (prevents data leakage)
- **Minimum per class**: 50 validation samples

### **Training Configuration**

```python
# Model
Architecture: EfficientNet-B4 (PyTorch)
Pretrained: ImageNet weights

```

### **Training Platform**

- **Platform**: Kaggle Notebooks
- **GPU**: NVIDIA P100 (16GB VRAM)
- **Training Time**: ~10.4 hours
- **Framework**: PyTorch 2.6+

---

## 🛠️ Development

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
cd backend
uvicorn app.main:app --reload --port 8000

# Run frontend (separate terminal)
cd frontend
python -m http.server 8080
```

### API Endpoints

```
GET  /                    - Health check
POST /api/v1/diagnose     - Upload image for diagnosis
GET  /api/v1/history      - Get diagnosis history
```

---

## ⚠️ Disclaimer

**For research and educational purposes only.**  
AI predictions are for **reference only** and **do not replace professional medical diagnosis**.  
Always consult a qualified dermatologist.

---

## 📚 References

- **Datasets:** [DermNet NZ](https://dermnetnz.org/), [ISIC 2019](https://challenge.isic-archive.com/), [PAD-UFES-20](https://data.mendeley.com/datasets/zr7vgbcyr2/1)
- **Models:** [EfficientNet](https://arxiv.org/abs/1905.11946), [YOLOv8](https://github.com/ultralytics/ultralytics)

---

**Last Updated:** February 2026  
**Model Version:** V2 (73.9% val acc)  
**Status:** ✅ Production Ready
