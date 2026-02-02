# 🏥 MedAI Dermatology - Hệ Thống AI Chẩn Đoán Bệnh Da

**Dự án phân loại 8 loại bệnh da bằng Deep Learning sử dụng EfficientNet-B3**

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
│   │   ├── efficientnet_b3_derma_v1.0_kaggle32e.keras  # Model phân loại chính
│   │   └── yolov8n-seg.pt             # Model Segmentation (tách vùng da)
│   │
│   ├── uploads/                   # Thư mục tạm lưu ảnh upload
│   ├── history.json                   # Local database (fallback) Lưu tạm khi MongoDB không khả dụng
│   ├── requirements.txt        # Dependencies cho Backend (FastAPI, TensorFlow inference, YOLO, etc.)
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
│       └── medai_nginx.conf           # Cấu hình Nginx
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
├── 📄 processed_isic_2019.zip         # Packed dataset cho Kaggle (tải qua link drive bên dưới)
├── 📄 README.md                       # Tài liệu hướng dẫn
└── 📄 requirements.txt                # Dependencies cho Backend

# Link drive dataset: https://drive.google.com/file/d/1EF-yuhAYhI7nmvR9vdlLZz9t81vSd_VK/view?usp=drive_link

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

## Quy Trình Làm Việc (Workflow)

### Tiền Xử Lý Dữ Liệu

```bash
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
   - Chia thành train/val/test (80/10/10)
   - Stratified split (giữ tỷ lệ classes)
   - Lưu vào `data/processed/`

**Kết quả:** Tạo ra 25.331 ảnh đã xử lý sẵn sàng cho training

---

### Training Model trên Kaggle

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

**Kết quả:**
- Final TTA Accuracy: 83.58% (TTA = Test Time Augmentation)
- Lưu model vào `backend/ml_models/efficientnet_b3_derma_v1.0_kaggle32e.keras` (32 epochs)


### Chạy Ứng Dụng

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


## 🔍 Inference Pipeline (Production Flow)

1. Người dùng upload ảnh từ Frontend
2. Backend lưu ảnh vào `backend/uploads/`
3. YOLOv8 Segmentation cắt vùng tổn thương
4. Resize & normalize ảnh
5. Load EfficientNet-B3 (.keras)
6. Dự đoán xác suất 8 classes
7. Trả kết quả JSON về Frontend




⚠️ Lưu ý:
Hệ thống này chỉ phục vụ mục đích nghiên cứu và hỗ trợ học tập.
<<<<<<< HEAD
Kết quả dự đoán không thay thế cho chẩn đoán của bác sĩ chuyên khoa.
=======
Kết quả dự đoán không thay thế cho chẩn đoán của bác sĩ chuyên khoa.
>>>>>>> 5e381fd5240510a27ebfaa77a51ea0e160eaf7dd
