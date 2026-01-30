# 🏥 MedAI Dermatology - Hệ Thống AI Chẩn Đoán Bệnh Da

**Dự án phân loại 7 loại bệnh da bằng Deep Learning sử dụng EfficientNet-B3**

**Giai đoạn hiện tại:** ✅ Đã hoàn thành tiền xử lý dữ liệu + Train trên Kaggle (đạt ~80% accuracy)

---

## 📊 Tổng Quan Dự Án

Đây là dự án nghiên cứu sử dụng AI để phân loại các bệnh về da dựa trên ảnh dermoscopy (ảnh da qua kính hiển vi). Dự án sử dụng dataset **HAM10000** với chính xác **10,015 ảnh** và 7 loại bệnh khác nhau.

**Kết quả đạt được:**
- ✅ Preprocessing hoàn tất với YOLO segmentation + hair removal
- ✅ Dataset đã xử lý: `processed_data.zip` (tất cả ảnh đã qua tiền xử lý)
- ✅ Model EfficientNet-B3 đạt **80.04%** test accuracy (70 epochs)
- ✅ Training trên Kaggle với GPU P100
- ⏳ Chưa deploy production

---

## 📁 Cấu Trúc Dự Án Chi Tiết

```
MedAI_Dermatology/
│
├── 📂 data/                        # THƯ MỤC DỮ LIỆU
│   ├── raw/                        # Dữ liệu gốc chưa xử lý
│   │   ├── images/                 # ~10,000 ảnh da gốc (ISIC 2018/HAM10000)
│   │   └── metadata.csv            # Thông tin bệnh nhân, nhãn bệnh
│   │
│   ├── masks/                      # Mask vùng tổn thương
│   │   └── lesion/                 # Ảnh mask đen trắng (vùng bệnh = trắng)
│   │
│   └── processed/                  # Dữ liệu đã tiền xử lý XONG
│       ├── train/                  # 70% data (~7,010 ảnh) - Để train model
│       │   ├── akiec/              # Từng folder cho từng loại bệnh
│       │   ├── bcc/
│       │   ├── bkl/
│       │   ├── df/
│       │   ├── mel/
│       │   ├── nv/
│       │   └── vasc/
│       ├── val/                    # 15% data (~1,502 ảnh) - Validation
│       └── test/                   # 15% data (~1,502 ảnh) - Test cuối cùng
│
├── 📂 src/                         # MÃ NGUỒN CHƯƠNG TRÌNH
│   ├── preprocessing/              # Code tiền xử lý ảnh
│   │   ├── hybrid_pipeline.py      # Pipeline chính
│   │   │                           # - Dùng YOLO để crop vùng bệnh
│   │   │                           # - Loại bỏ lông (hair removal)
│   │   │                           # - Resize về 300x300
│   │   │                           # - Split train/val/test
│   │   ├── yolo_segmentor.py       # YOLO segmentation
│   │   └── process_dataset.py      # Xử lý dataset
│   │
│   ├── models/                     # Định nghĩa các model AI
│   │   ├── efficientnet_clf.py     # EfficientNet-B3 classifier
│   │   └── unet_segmentor.py       # U-Net segmentation
│   │
│   ├── utils/                      # Tiện ích
│   │   └── tf_config.py            # Config TensorFlow/GPU
│   └── train.py                    # SCRIPT TRAIN CHÍNH
│                                   # - Load data từ processed/
│                                   # - Train model 2 phase
│                                   # - Save model vào models/
│
├── 📂 notebooks/                   # JUPYTER NOTEBOOKS
│   ├── 01_eda_data.ipynb          # Phân tích dữ liệu ban đầu
│   │                               # - Check số lượng ảnh mỗi class
│   │                               # - Visualize mẫu ảnh
│   │                               # - Kiểm tra imbalanced data
│   │
│   ├── 02_processed_data_check.ipynb  # Kiểm tra data sau preprocessing
│   │                                  # - Verify dimensions (300x300)
│   │                                  # - Check class distribution
│   │                                  # - Xem samples đã xử lý
│   │
│   └── kaggle-train-efficientnet.ipynb  # NOTEBOOK TRAIN CHÍNH
│                                        # - Chạy trên Kaggle với GPU P100
│                                        # - 2-phase training
│                                        # - Data augmentation
│                                        # - Đạt ~80% accuracy
│
├── 📂 models/                      # LƯU MODEL ĐÃ TRAIN
│   └── yolov8n-seg.pt              # Model YOLO segmentation (6.8MB)
│                                   # Dùng để crop vùng bệnh trong preprocessing
│
├── 📂 backend/                     # BACKEND API (CHƯA TRIỂN KHAI)
│   ├── app/                        # Thư mục ứng dụng FastAPI
│   │   ├── __init__.py            # Package initialization
│   │   ├── main.py                # FastAPI app chính, định nghĩa endpoints
│   │   │                          # - POST /api/v1/predict (upload ảnh, trả về dự đoán)
│   │   │                          # - GET /api/v1/history (lịch sử chẩn đoán)
│   │   │                          # - GET /api/v1/statistics (thống kê)
│   │   ├── config.py              # Configuration (MongoDB URI, model path, v.v.)
│   │   ├── database.py            # MongoDB connection manager
│   │   │
│   │   ├── models/                # Pydantic schemas (request/response models)
│   │   │   ├── __init__.py
│   │   │   └── schemas.py         # PredictionRequest, PredictionResponse, etc.
│   │   │
│   │   ├── services/              # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── preprocessing.py   # Tiền xử lý ảnh upload (resize, normalize)
│   │   │   ├── inference.py       # Load model, chạy prediction
│   │   │   └── storage.py         # Lưu/lấy data từ MongoDB
│   │   │
│   │   └── utils/                 # Utilities
│   │       ├── __init__.py
│   │       └── constants.py       # Class names, recommendations, v.v.
│   │
│   ├── ml_models/                 # Lưu model để deploy
│   │   ├── efficientnet_b3_derma_finetuned.keras  # Model đã train
│   │   └── README.md              # Hướng dẫn về model
│   │
│   ├── tests/                     # Unit tests
│   │   ├── test_preprocessing.py
│   │   ├── test_inference.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt           # Python dependencies cho backend
│   ├── .env.example               # Template cho environment variables
│   ├── Dockerfile                 # Docker image cho backend
│   └── README.md                  # Hướng dẫn backend
│
├── 📂 frontend/                    # FRONTEND WEB (CHƯA TRIỂN KHAI)
│   ├── index.html                 # Trang chính
│   ├── pages/                     # Trang chính
│   │   ├── diagnose.html          # Trang upload & chẩn đoán
│   │   ├── result.html            # Trang hiển thị kết quả
│   │   ├── history.html           # Trang lịch sử chẩn đoán
│   │
│   ├── css/                       # Stylesheets
│   │   ├── style.css              # Main styles
│   │   ├── diagnose.css           # Styles cho trang chẩn đoán
│   │   └── responsive.css         # Responsive design
│   │
│   ├── js/                        # JavaScript
│   │   ├── app.js                 # Main app logic
│   │   ├── config.js              # API endpoint configs
│   │   ├── diagnose.js            # Upload & call API logic
│   │   ├── result.js              # Hiển thị kết quả
│   │   └── history.js             # Lấy & hiển thị lịch sử
│   │
│   ├── assets/                    # Static assets
│   │   ├── images/                # Logos, icons, placeholders
│   │   └── fonts/                 # Custom fonts (nếu có)
│   │
│   └── README.md                  # Hướng dẫn frontend
│
├── 📂 infrastructure/              # CẤU HÌNH DEPLOYMENT (CHƯA DÙNG)
│   ├── nginx/                      # Nginx config
│   │   └── nginx.conf             # Reverse proxy, serve static files
│   ├── docker-compose.yml          # Docker multi-container setup
│   │                              # - MongoDB service
│   │                              # - Backend service
│   │                              # - Nginx service
│   └── .env                        # Environment variables cho deployment
│
├── 📂 reports/                     # BÁO CÁO & KẾT QUẢ
│   ├── figures/                    # Charts, graphs (chưa có data)
│   └── tables/                     # Metrics CSV (chưa có data)
│
├── 📄 requirements.txt             # DANH SÁCH THƯ VIỆN PYTHON CẦN CÀI
├── 📄 .gitignore                   # Git ignore rules
├── 📄 visualize_preprocessing.py   # Script visualize preprocessing
└── 📄 README.md                    # File này (tài liệu chính)
```

---

## 🎯 Dataset: HAM10000

**Nguồn:** HAM10000 (Human Against Machine with 10,000 training images)

**File dữ liệu:**
- `processed_data.zip` - Chứa tất cả 10,015 ảnh đã qua tiền xử lý
- Đã crop vùng tổn thương, loại bỏ lông, resize 300x300
- Chia sẵn thành train/val/test folders

### 7 Loại Bệnh Da (Classes):

| Mã | Tên Tiếng Việt | Tên Tiếng Anh | Mức độ nguy hiểm |
|----|----------------|---------------|------------------|
| `akiec` | Ung thư biểu mô | Actinic Keratoses | ⚠️ Cao |
| `bcc` | Ung thư tế bào đáy | Basal Cell Carcinoma | ⚠️ Cao |
| `bkl` | Sừng hóa lành tính | Benign Keratosis | ✅ Thấp |
| `df` | U xơ sợi da | Dermatofibroma | ✅ Thấp |
| `mel` | Ung thư hắc tố (Melanoma) | Melanoma | 🔴 Rất cao |
| `nv` | Nốt ruồi lành tính | Melanocytic Nevus | ✅ Thấp |
| `vasc` | Tổn thương mạch máu | Vascular Lesions | ⚠️ Trung bình |

### Phân Chia Dữ Liệu:

```
Tổng: 10,015 ảnh (chính xác)
├── Train:      70% (~7,010 ảnh) - Để huấn luyện model
├── Validation: 15% (~1,502 ảnh) - Để theo dõi trong quá trình train
└── Test:       15% (~1,503 ảnh) - Đánh giá cuối cùng
```

---

## � Quy Trình Làm Việc (Workflow)

### Bước 1: Tiền Xử Lý Dữ Liệu

```bash
# Chạy preprocessing pipeline
python src/preprocessing/hybrid_pipeline.py
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
- Upload `processed_data.zip` lên Kaggle Dataset
- File chứa tất cả 10,015 ảnh đã preprocessing
- Extract trong notebook để dùng

```bash
# Mở notebook trên Kaggle:
# notebooks/kaggle-train-efficientnet.ipynb

# Trong notebook Kaggle:
# 1. Add dataset: processed_data.zip
# 2. Extract: !unzip ../input/your-dataset/processed_data.zip
# 3. Run training code
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
Dense(7, activation='softmax')  ← 7 classes
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