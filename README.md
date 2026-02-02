# 🏥 MedAI Dermatology - Hệ Thống AI Chẩn Đoán Bệnh Da

**Dự án phân loại 7 loại bệnh da bằng Deep Learning sử dụng EfficientNet-B3**

**Giai đoạn hiện tại:** ✅ Đã nâng cấp lên dataset ISIC 2019 (25k ảnh) để cải thiện độ chính xác.


## 📊 Tổng Quan Dự Án

Đây là dự án nghiên cứu sử dụng AI để phân loại các bệnh về da dựa trên ảnh dermoscopy. Dự án sử dụng dataset **ISIC 2019** với **25,331 ảnh** và **8 loại bệnh**.

**Kết quả đạt được:**
- ✅ Dataset ISIC 2019.
- ✅ Quy trình tiền xử lý tự động (Resize 300x300, Stratified Split).
- ✅ Model EfficientNet-B3.
- ✅ Training trên Kaggle tối ưu hóa.


## 📁 Cấu Trúc Dự Án Chi Tiết

MedAI_Dermatology/
│
├── 📂 backend/                    # 🖥️ BACKEND SYSTEM (FastAPI)
│   ├── app/                           # Source code chính của backend
│   │   ├── models/                    # Pydantic schemas (Request/Response models)
│   │   ├── services/                  # Business Logic (Inference, Preprocessing, Storage)
│   │   ├── utils/                     # Utility functions
│   │   ├── config.py                  # Cấu hình hệ thống (Settings)
│   │   ├── database.py                # Quản lý kết nối MongoDB
│   │   └── main.py                    # Entry point, định nghĩa API Endpoints
│   │
│   ├── ml_models/                 # 🧠 KHO CHỨA MODELS AI
│   │   ├── efficientnet_b3_derma_v1.0_kaggle32e.keras # Model phân loại chính
│   │   └── yolov8n-seg.pt             # Model Segmentation (tách vùng da)
│   │
│   ├── uploads/                   # Thư mục tạm lưu ảnh upload
│   ├── history.json                   # Local database (fallback)
│   ├── requirements.txt               # Dependencies cho Backend
│   ├── start_backend.sh               # Script khởi động Backend
│   └── .env                           # Biến môi trường (DB URL, Secrets)
│
├── 📂 frontend/                  # 🌐 GIAO DIỆN NGƯỜI DÙNG
│   ├── assets/                        # Images, logos
│   ├── css/                           # Stylesheets
│   ├── js/                            # JavaScript logic (App, API, Diagnose)
│   ├── pages/                         # HTML sub-pages (Diagnose, History, Result)
│   ├── index.html                     # Trang chủ
│   └── start_frontend.sh       # Script khởi động Frontend server
│
├── 📂 src/                            # ⚙️ DEV & TRAINING CORE (Trái tim của dự án AI)
│   │  *Vai trò: Chứa toàn bộ mã nguồn xử lý dữ liệu, định nghĩa model và training.*
│   │
│   ├── 📄 train.py                    # 🚀 Script huấn luyện chính
│   │   # - Đọc dữ liệu từ data/processed
│   │   # - Xây dựng model từ src/models
│   │   # - Chạy training loop và lưu model (.keras)
│   │
│   ├── 📂 preprocessing/              # 🛠️ Module Tiền xử lý ảnh (Preprocessing)
│   │   # Biến ảnh thô thành ảnh sạch để AI học tốt hơn.
│   │   ├── 📄 hybrid_pipeline.py      # Pipeline xử lý lai (Hybrid): Hair removal, Color balance...
│   │   ├── 📄 yolo_segmentor.py       # Chạy model YOLOv8 để cắt vùng bệnh (Segmentation)
│   │   ├── 📄 process_dataset.py      # Script xử lý hàng loạt dataset thô sang sạch
│   │   └── 📄 prepare_isic_data.py    # Script chuyên biệt cho bộ dữ liệu ISIC 2019
│   │
│   ├── 📂 models/                     # 🧠 Kiến trúc Model (Model Architectures)
│   │   # Nơi định nghĩa "hình dáng" của mạng nơ-ron.
│   │   ├── 📄 efficientnet_clf.py     # Kiến trúc EfficientNet-B3 (Phân loại bệnh)
│   │   └── 📄 unet_segmentor.py       # Kiến trúc U-Net (Phân vùng ảnh - nếu tự train)
│   │
│   ├── 📂 data_management/            # 💾 Quản lý dữ liệu
│   │   └── 📄 merge_and_reconstruct.py # Công cụ gộp/tái cấu trúc dataset
│   │
│   └── 📂 utils/                      # 🔧 Tiện ích chung
│       └── 📄 tf_config.py            # Cấu hình TensorFlow (GPU memory growth, etc.)
│
├── 📂 infrastructure/                 # 🏗️ DEVOPS & DEPLOYMENT
│   ├── docker/                        # Config files cho Docker
│   └── nginx/                         # Config Nginx
│
├── 📂 research/                   # 🔬 NGHIÊN CỨU & KẾT QUẢ
│   ├── 📂 notebooks/                  # Jupyter Notebooks
│   │   ├── 01_eda_data.ipynb          # Phân tích dữ liệu
│   │   ├── 02_processed_data_check.ipynb # Kiểm tra dữ liệu sau xử lý
│   │   └── isic-2019-efficientnetb3-kaggle-train.ipynb # Notebook training chính
│   └── 📂 reports/                    # Báo cáo & Kết quả visualize
│       ├── 📂 gradcam/                # Kết quả Grad-CAM (Heatmaps)
│       └── preprocessing_pipeline.png # Sơ đồ luồng xử lý ảnh
│
├── 📂 data/                       # 💾 KHO DỮ LIỆU
│   ├── raw/                           # Dữ liệu thô (Images, Metadata)
│   ├── processed/                     # Dữ liệu đã xử lý (Train/Val/Test split)
│   └── masks/                         # Dữ liệu phân vùng (Segmentation)
│       └── lesion/                    # Mask vùng bệnh (Ground Truth)
│
├── 📄 visualize_preprocessing.py       # Script demo xử lý ảnh
├── 📄 processed_isic_2019.zip         # Packed dataset cho Kaggle
└── 📄 README.md                       # Tài liệu chính
---

## 🎯 Dataset: ISIC 2019

**Nguồn:** ISIC 2019 Challenge (bao gồm HAM10000, BCN_20000, MSK).

**File dữ liệu:**
- `processed_isic_2019.zip` - Chứa 25,331 ảnh đã resize 300x300
- Đã chia sẵn thành train/val/test folders theo tỷ lệ 80/10/10

### 8 Loại Bệnh Da (Classes):

| Mã | Tên Tiếng Việt | Tên Tiếng Anh | Mức độ nguy hiểm |
|----|----------------|---------------|------------------|
| `akiec` | Dày sừng quang hóa | Actinic Keratoses | ⚠️ Cao |
| `bcc` | Ung thư tế bào đáy | Basal Cell Carcinoma | ⚠️ Cao |
| `bkl` | Sừng hóa lành tính | Benign Keratosis | ✅ Thấp |
| `df` | U xơ sợi da | Dermatofibroma | ✅ Thấp |
| `mel` | Ung thư hắc tố (Melanoma) | Melanoma | 🔴 Rất cao |
| `nv` | Nốt ruồi lành tính | Melanocytic Nevus | ✅ Thấp |
| `scc` | Ung thư biểu mô TB vảy | Squamous Cell Carcinoma | ⚠️ Cao |
| `vasc` | Tổn thương mạch máu | Vascular Lesions | ⚠️ Trung bình |

### Phân Chia Dữ Liệu:

```
Tổng: 25,331 ảnh
├── Train:      80% (~20,264 ảnh)
├── Validation: 10% (~2,533 ảnh)
└── Test:       10% (~2,534 ảnh)
```

---

## � Quy Trình Làm Việc (Workflow)

### Bước 1: Tiền Xử Lý Dữ Liệu

```bash
# Chạy preprocessing pipeline
# Chạy ISIC preprocessing script
python src/preprocessing/prepare_isic_data.py
```

**Pipeline gồm các bước:**

1. **YOLO Segmentation**: 
   - Dùng YOLOv8n-seg để tìm vùng tổn thương
   - Crop ảnh chỉ giữ lại vùng bệnh
   - Loại bỏ background không cần thiết

2. **Hair Removal**:
   - Thuật toán DullRazor
   - Loại bỏ lông trên da
   - Giúp model focus vào vùng bệnh

3. **Resize & Normalize**:
   - Resize tất cả ảnh về 300x300 pixels
   - Chuẩn hóa giá trị pixel (0-1)
   - Chuẩn bị cho EfficientNet

4. **Split Dataset**:
   - Chia thành train/val/test (70/15/15)
   - Stratified split (giữ tỷ lệ classes)
   - Lưu vào `data/processed/`

**Kết quả:** Tạo ra ~10,000 ảnh đã xử lý sẵn sàng cho training

---

### Bước 2: Training Model trên Kaggle

**Dataset trên Kaggle:**
**Dataset trên Kaggle:**
- Upload `processed_isic_2019.zip` lên Kaggle Dataset
- File chứa 25k ảnh đã preprocessing
- Extract trong notebook để dùng

```bash
# Mở notebook trên Kaggle:
# research/notebooks/kaggle-train-efficientnet.ipynb

# Trong notebook Kaggle:
# Add dataset: processed_isic_2019.zip
# Run training code
```

**Kiến Trúc Model:**

```
Input: Ảnh 300x300x3 (RGB)
    ↓
EfficientNet-B3 (pretrained ImageNet)
    ↓ (freeze base trong Phase 1)
GlobalAveragePooling2D
    ↓
Dense(512, activation='relu')
    ↓
Dropout(0.5)  ← Tránh overfitting
    ↓
Dense(8, activation='softmax')  ← 8 classes
    ↓
Output: Xác suất cho 7 loại bệnh
```

**Chiến Lược Training (2 Phases):**

**Phase 1: Transfer Learning (50 epochs)**
- Freeze toàn bộ EfficientNet-B3 base
- Chỉ train phần classifier (Dense layers)
- Learning rate: 0.001
- Optimizer: Adam
- Goal: Học features cơ bản

**Phase 2: Fine-Tuning (20 epochs)**
- Unfreeze 50 layers cuối của base
- Train tiếp với learning rate thấp hơn: 0.0001
- Optimizer: Adam
- Goal: Tinh chỉnh features cho skin lesions

**Data Augmentation:**
```python
# Augmentation khi training (chỉ train set)
- Rotation: ±20°
- Width/Height Shift: 20%
- Zoom: 20%
- Horizontal Flip: Random
- Brightness: ±20%
```

**Class Weights:**
- Xử lý imbalanced data
- Class `nv` (nhiều nhất) có weight thấp
- Class `mel`, `akiec` (ít hơn) có weight cao

**Kết Quả Training:**

| Metric | Giá trị |
|--------|---------|
| **Test Accuracy** | **80.04%** (chính xác) |
| **Total Epochs** | 70 epochs |
| **AUC Score** | ~0.97 |
| **Best Epoch** | ~Epoch 60-65 |
| **Training Time** | 40-60 phút (Kaggle P100 GPU) |
| **Model Size** | ~125MB (.h5 format) |

---

### Bước 3: Chạy Ứng Dụng (Deployment)

Bạn cần mở 2 cửa sổ terminal để chạy cả Backend và Frontend.

#### 1. Chạy Backend (Terminal 1)
Script này sẽ tự động tạo virtual environment, cài thư viện và start server:

```bash
cd backend
chmod +x start_backend.sh  # Cấp quyền thực thi nếu cần
./start_backend.sh
```
*Backend sẽ chạy tại: `http://localhost:8000`*

#### 2. Chạy Frontend (Terminal 2)
Script này sẽ start một web server đơn giản cho frontend:

```bash
cd frontend
chmod +x start_frontend.sh # Cấp quyền thực thi nếu cần
./start_frontend.sh
```
*Frontend sẽ chạy tại: `http://localhost:3000`*

## 🏗️ Chi Tiết Hạ Tầng (Infrastructure)

### Nginx Configuration (`infrastructure/nginx/medai_nginx.conf`)

File cấu hình Nginx đóng vai trò là **Web Server & Reverse Proxy**, giúp hệ thống hoạt động ổn định và bảo mật hơn.

**Chức năng chính:**

1.  **Serve Frontend (Giao diện):**
    *   Trỏ root về folders: `/home/khangjv/WorkSpace/MedAI_Dermatology/frontend`
    *   Khi truy cập `http://localhost`, Nginx sẽ tải file `index.html` từ thư mục này.

2.  **Reverse Proxy cho Backend (API):**
    *   Chuyển tiếp (forward) các request từ `/api/` đến Backend server (`http://localhost:8000`).
    *   Giúp Frontend gọi API mà không gặp lỗi Cross-Origin Resource Sharing (CORS).
    *   **Settings quan trọng:**
        *   `client_max_body_size 10M;`: Cho phép upload ảnh lên đến 10MB (cần thiết cho ảnh da liễu độ phân giải cao).

3.  **Caching Tĩnh (Static Files):**
    *   Tối ưu hóa tốc độ tải trang bằng cách cache các file tĩnh (ảnh, CSS, JS) trong 1 năm.

**Sơ đồ luồng dữ liệu:**
```
User -> Nginx (Port 80)
        ├── /       -> Frontend (Static Files)
        └── /api/*  -> Backend (Python FastAPI - Port 8000)
```

## Công Nghệ

- **HTML/CSS**: Tailwind CSS (via CDN)
- **JavaScript**: Vanilla JS (ES6+)
- **Design**: Google Material Symbols, Inter font
- **Backend API**: FastAPI tại `http://localhost:8000`
- **FastAPI**: Web framework hiện đại, nhanh
- **TensorFlow**: Load và chạy model EfficientNet-B3
- **MongoDB** (optional): Lưu lịch sử chẩn đoán
- **Fallback JSON**: Tự động dùng file JSON nếu không có MongoDB