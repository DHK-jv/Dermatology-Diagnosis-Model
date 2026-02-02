# 🏥 MedAI Dermatology - Hệ Thống AI Chẩn Đoán Bệnh Da

> **Author:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Dự án:** Phân loại 8 loại bệnh da liễu bằng Deep Learning (EfficientNet-B3)

---

## 📊 Tổng Quan Dự Án

Đây là dự án nghiên cứu và phát triển hệ thống AI hỗ trợ chẩn đoán bệnh da liễu dựa trên ảnh dermoscopy. Hệ thống tích hợp quy trình xử lý ảnh y tế chuyên sâu và mô hình Deep Learning tiên tiến.

**Kết quả đạt được:**
- ✅ **Dataset:** Nâng cấp lên ISIC 2019 (25,331 ảnh).
- ✅ **Preprocessing:** Tự động hóa (YOLOv8 Segmentation + Hair Removal).
- ✅ **Model:** EfficientNet-B3 được tối ưu hóa trên Kaggle.
- ✅ **System:** Full-stack System với Backend (FastAPI) và Frontend hoàn chỉnh.

---

## 🚀 Quick Start

```bash
git clone https://github.com/DHK-jv/Dermatology-Diagnosis-Model.git
cd Dermatology-Diagnosis-Model
```
Sau khi clone về, từ thư mục gốc của dự án, chạy lệnh:

```bash
python run.py
# Hoặc: python3 run.py

```

## 📁 Cấu Trúc Dự Án Chi Tiết

```bash
MedAI_Dermatology/
│
├── 📂 backend/                    # 🖥️ BACKEND SYSTEM (FastAPI)
│   ├── app/                       # Source code chính của backend
│   │   ├── models/                # Pydantic schemas (Request/Response models)
│   │   ├── services/              # Business Logic (Inference, Preprocessing, Storage)
│   │   ├── utils/                 # Utility functions
│   │   ├── config.py              # Cấu hình hệ thống (Settings)
│   │   ├── database.py            # Quản lý kết nối MongoDB
│   │   └── main.py                # Entry point, định nghĩa API Endpoints
│   │
│   ├── ml_models/                 # 🧠 KHO CHỨA MODELS AI
│   │   ├── efficientnet_b3_derma_v1.0_kaggle32e.keras  # Model phân loại chính
│   │   └── yolov8n-seg.pt         # Model Segmentation (tách vùng da)
│   │
│   ├── uploads/                   # Thư mục tạm lưu ảnh upload
│   ├── history.json               # Local database (fallback)
│   ├── requirements.txt           # Dependencies cho Backend
│   ├── start_backend.sh           # Script khởi động Backend (Legacy)
│   └── .env                       # Biến môi trường (DB URL, Secrets)
│
├── 📂 frontend/                   # 🌐 GIAO DIỆN NGƯỜI DÙNG
│   ├── assets/                    # Images, logos
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript logic (App, API, Diagnose)
│   ├── pages/                     # HTML sub-pages (Diagnose, History, Result)
│   ├── index.html                 # Trang chủ
│   └── start_frontend.sh          # Script khởi động Frontend (Legacy)
│
├── 📂 src/                        # ⚙️ DEV & TRAINING CORE (Trái tim của dự án AI)
│   │  *Vai trò: Chứa toàn bộ mã nguồn xử lý dữ liệu, định nghĩa model và training.*
│   │
│   ├── 📄 train.py                # 🚀 Script huấn luyện chính
│   │   # - Đọc dữ liệu từ data/processed
│   │   # - Xây dựng model từ src/models
│   │   # - Chạy training loop và lưu model (.keras)
│   │
│   ├── 📂 preprocessing/          # 🛠️ Module Tiền xử lý ảnh (Preprocessing)
│   │   # Biến ảnh thô thành ảnh sạch để AI học tốt hơn.
│   │   ├── 📄 hybrid_pipeline.py  # Pipeline xử lý lai: Hair removal, Color balance...
│   │   ├── 📄 yolo_segmentor.py   # Chạy model YOLOv8 để cắt vùng bệnh
│   │   ├── 📄 process_dataset.py  # Script xử lý hàng loạt dataset thô sang sạch
│   │   └── 📄 prepare_isic_data.py # Script chuyên biệt cho bộ dữ liệu ISIC 2019
│   │
│   ├── 📂 models/                 # 🧠 Kiến trúc Model (Model Architectures)
│   │   # Nơi định nghĩa "hình dáng" của mạng nơ-ron.
│   │   ├── 📄 efficientnet_clf.py # Kiến trúc EfficientNet-B3 (Phân loại bệnh)
│   │   └── 📄 unet_segmentor.py   # Kiến trúc U-Net (Phân vùng ảnh - nếu tự train)
│   │
│   ├── 📂 data_management/        # 💾 Quản lý dữ liệu
│   │   └── 📄 merge_and_reconstruct.py # Công cụ gộp/tái cấu trúc dataset
│   │
│   └── 📂 utils/                  # 🔧 Tiện ích chung
│       └── 📄 tf_config.py        # Cấu hình TensorFlow (GPU memory growth, etc.)
│
├── 📂 infrastructure/             # 🏗️ DEVOPS & DEPLOYMENT
│   ├── docker/                    # Config files cho Docker
│   └── nginx/                     # Config Nginx
│       └── medai_nginx.conf       # Cấu hình Nginx
│
├── 📂 research/                   # 🔬 NGHIÊN CỨU & KẾT QUẢ
│   ├── 📂 notebooks/              # Jupyter Notebooks
│   │   ├── 01_eda_data.ipynb      # Phân tích dữ liệu
│   │   ├── 02_processed_data_check.ipynb # Kiểm tra dữ liệu sau xử lý
│   │   └── isic-2019-efficientnetb3-kaggle-train.ipynb # Notebook training chính
│   └── 📂 reports/                # Báo cáo & Kết quả visualize
│       ├── 📂 gradcam/            # Kết quả Grad-CAM (Heatmaps)
│       └── preprocessing_pipeline.png # Sơ đồ luồng xử lý ảnh
│
├── 📂 data/                       # 💾 KHO DỮ LIỆU
│   ├── raw/                       # Dữ liệu thô (Images, Metadata)
│   ├── processed/                 # Dữ liệu đã xử lý (Train/Val/Test split)
│   └── masks/                     # Dữ liệu phân vùng (Segmentation)
│       └── lesion/                # Mask vùng bệnh (Ground Truth)
│
├── 📄 visualize_preprocessing.py   # Script demo xử lý ảnh
├── 📄 processed_isic_2019.zip     # Packed dataset cho Kaggle
├── 📄 README.md                   # Tài liệu hướng dẫn
├── 📄 requirements.txt            # Dependencies cho Backend
└── 📄 run.py                      # ⚡ Script chạy toàn bộ hệ thống (New)

```

---

## 🎯 Thông Tin Dataset: ISIC 2019

* **Nguồn:** ISIC 2019 Challenge (HAM10000, BCN_20000, MSK).
* **Link tải:** https://drive.google.com/file/d/1EF-yuhAYhI7nmvR9vdlLZz9t81vSd_VK/view?usp=drive_link

### 🏥 8 Loại Bệnh Da (Classes)

| Mã | Tên Tiếng Việt | Tên Tiếng Anh | Mức độ nguy hiểm |
| --- | --- | --- | --- |
| `mel` | **Ung thư hắc tố** | Melanoma | 🔴 Rất cao |
| `bcc` | Ung thư tế bào đáy | Basal Cell Carcinoma | ⚠️ Cao |
| `scc` | Ung thư biểu mô TB vảy | Squamous Cell Carcinoma | ⚠️ Cao |
| `akiec` | Dày sừng quang hóa | Actinic Keratoses | ⚠️ Cao |
| `vasc` | Tổn thương mạch máu | Vascular Lesions | ⚠️ Trung bình |
| `nv` | Nốt ruồi lành tính | Melanocytic Nevus | ✅ Thấp |
| `bkl` | Sừng hóa lành tính | Benign Keratosis | ✅ Thấp |
| `df` | U xơ sợi da | Dermatofibroma | ✅ Thấp |

### 📉 Phân Chia Dữ Liệu

Dữ liệu được chia theo tỷ lệ **80/10/10** (Stratified Split):

Cấu trúc Dataset (25,331 ảnh)
- Train (80%): 20264
- Validation (10%): 2533
- Test (10%): 2534

---

## ⚙️ Pipeline 

## Quy trình tiền xử lý ảnh

```bash
python src/preprocessing/prepare_isic_data.py


1. YOLO Segmentation: Dùng `yolov8n-seg` để phát hiện và tách nền, chỉ giữ lại vùng tổn thương.
2. Hair Removal: Thuật toán DullRazor loại bỏ lông, tránh gây nhiễu cho model.
3. Chuẩn hóa: Resize về `300x300` và chuẩn hóa pixel `[0-1]`.
4. Inference: Model EfficientNet-B3 đưa ra xác suất cho 8 lớp bệnh.

---

## 🔬 Training & Kết quả

* **Nền tảng:** Kaggle GPU (P100).
* **Notebook:** `research/notebooks/kaggle-train-efficientnet.ipynb`
* **Model:** EfficientNet-B3 (Pre-trained ImageNet).
* **Kết quả:** Final TTA Accuracy: **83.58%**.

```

## ⚠️ Lưu Ý Quan Trọng

Disclaimer: Hệ thống này được xây dựng nhằm mục đích nghiên cứu và hỗ trợ học tập. Kết quả dự đoán của AI chỉ mang tính chất tham khảo và không thay thế cho chẩn đoán của bác sĩ chuyên khoa.