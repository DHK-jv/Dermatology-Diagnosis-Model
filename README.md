# 🏥 MedAI Dermatology - AI Chẩn Đoán Bệnh Da Liễu

> **Tác giả:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Hệ thống Phân loại Bệnh Da liễu dựa trên Deep Learning**

---

## 📊 Tổng quan

Một hệ thống AI chẩn đoán bệnh da liễu sử dụng các kỹ thuật học sâu (deep learning) và xử lý ảnh y tế tiên tiến. Hệ thống tích hợp các luồng tiền xử lý (preprocessing) chuyên nghiệp và mô hình mạng nơ-ron hiện đại để hỗ trợ các bác sĩ trong việc chẩn đoán.

**Các thành tựu chính:**
- ✅ **Bộ dữ liệu (Dataset):** ~41.000 ảnh (DermNet NZ + ISIC 2019 + PAD-UFES-20)
- ✅ **Tiền xử lý (Preprocessing):** Luồng tự động (Cắt phân đoạn bằng YOLOv8 + Tẩy lông + Kiểm soát chất lượng)
- ✅ **Mô hình (Model):** EfficientNet-B4 V2.1 (Độ chính xác xác thực - validation accuracy đạt 86,2%, F1 0,880)
- ✅ **Hệ thống:** Ứng dụng Full-stack với backend dùng FastAPI và frontend web hiện đại
- ✅ **Phân loại:** 24 loại bệnh da liễu được dịch song ngữ Việt - Anh

---

## 🚀 Bắt đầu nhanh

```bash
git clone https://github.com/DHK-jv/Dermatology-Diagnosis-Model.git
cd Dermatology-Diagnosis-Model
python run.py
```

Hệ thống sẽ tự khởi động tại địa chỉ: http://localhost:8080

---

## 🤖 Tải mô hình

Trọng số của mô hình (Model weights) **không được kèm theo** trong kho lưu trữ này (do kích thước quá lớn). Vui lòng tải xuống thủ công trước khi chạy:

1. **Tải xuống:** `efficientnet_b4_derma_v2_1_finetuned.pth` (71MB, link cập nhật sau)
2. **Gắn vào thư mục:** `backend/ml_models/efficientnet_b4_derma_v2_1_finetuned.pth`

---

## 🏥 Các bệnh hỗ trợ (24 Nhóm)

| Tên Tiếng Việt | Tên Tiếng Anh | Mức độ Nguy hiểm |
|-----------|---------|------|
| Mụn trứng cá & Rosacea | Acne Rosacea | Thấp |
| Dày sừng quang hóa | Actinic Keratosis | Trung bình ⚠️ |
| Rụng tóc | Alopecia Hair Loss | Thấp |
| **Ung thư tế bào đáy** | **Basal Cell Carcinoma** | **Cao ⚠️** |
| Bệnh bóng nước | Bullous Disease | Trung bình |
| Viêm mô tế bào | Cellulitis Impetigo | Trung bình |
| Viêm da tiếp xúc | Contact Dermatitis | Thấp |
| U xơ da lành tính | Dermatofibroma | Thấp |
| Chàm & Viêm da cơ địa | Eczema Atopic Dermatitis | Thấp |
| Phát ban do thuốc | Drug Eruptions | Trung bình |
| Nấm da | Fungal Infections | Thấp |
| Côn trùng cắn | Infestations Bites | Thấp |
| Lupus & Bệnh mô liên kết | Lupus | Cao ⚠️ |
| Nốt ruồi lành tính | Melanocytic Nevus | Thấp |
| **Ung thư hắc tố** | **Melanoma** | **Vô cùng nguy hiểm 🚨** |
| Rối loạn sắc tố | Pigmentation Disorders | Thấp |
| Vảy nến | Psoriasis Lichen Planus | Trung bình |
| Dày sừng tiết bã | Seborrheic Keratosis | Thấp |
| **Ung thư tế bào vảy** | **Squamous Cell Carcinoma** | **Cao ⚠️** |
| Biểu hiện da bệnh nội khoa | Systemic Disease | Cao |
| Mề đay | Urticaria Hives | Thấp |
| Tổn thương mạch máu | Vascular Lesion | Trung bình |
| Viêm mạch máu | Vasculitis | Cao |
| Nhiễm trùng virus | Viral Infections | Thấp |

---

## 📁 Cấu trúc thư mục dự án

```
MedAI_Dermatology/
│
├── 📂 backend/                      # Hệ thống Backend (FastAPI)
│   ├── app/
│   │   ├── models/                  # Các schema của Pydantic 
│   │   ├── services/                # Xử lý Logic chính
│   │   │   ├── inference.py         # Chạy AI suy luận
│   │   │   ├── preprocessing.py     # Tiền xử lý ảnh
│   │   │   └── storage.py           # Lưu trữ dữ liệu DB
│   │   ├── utils/
│   │   │   └── constants.py         # Các file config và mapping tên bệnh
│   │   ├── config.py                # File cấu hình toàn hệ thống
│   │   └── main.py                  # Các endpoint API
│   │
│   ├── ml_models/                   # Mô hình AI
│   │   ├── efficientnet_b4_derma_v2_1_finetuned.pth    # Mô hình phân loại chính (V2.1)
│   │   └── yolov8n-seg.pt           # Mô hình cắt phân đoạn ảnh
│   │
│   └── uploads/                     # Thư mục lưu file tạm
│
├── 📂 frontend/                     # Giao diện người dùng Web
│   ├── assets/                      # Hình ảnh, logo
│   ├── css/                         # File định dạng CSS
│   ├── js/                          # JavaScript
│   │   ├── app.js                   # Logic app chính
│   │   ├── api.js                   # Kết nối API Backend
│   │   └── diagnose.js              # Luồng giao diện lúc chẩn đoán
│   ├── pages/                       # Các trang HTML
│   │   ├── diagnose.html            # Trang màn chẩn đoán
│   │   ├── history.html             # Trang xem lịch sử
│   │   └── result.html              # Trang kết quả
│   └── index.html                   # Trang chủ (Landing page)
│
├── 📂 preprocessing/                # Đoạn mã gốc xử lý ảnh
│   ├── hybrid_pipeline.py           # Luồng xử lý dữ liệu hỗn hợp chính
│   └── yolo_segmentor.py            # Hàm xử lý YOLO 
│
├── 📂 research/                     # Nghiên cứu và Huấn luyện AI
│   ├── notebooks/
│   │   ├── kaggle-train.ipynb       # Khối Notebook train chính trên Kaggle
│   │   ├── 01_eda_data.ipynb        # Phân tích dữ liệu (EDA)
│   │   └── 02_processed_data_check.ipynb
│   └── reports/                     # Báo cáo sau quá trình train
│
├── 📂 data/                         # Bộ dữ liệu ban đầu
│   ├── raw/                         # Ảnh thô chưa qua làm sạch
│   │   ├── dermnet/                 # Nguồn DermNet NZ
│   │   ├── isic_2019/               # Nguồn ISIC 2019
│   │   └── pad_ufes/                # Nguồn PAD-UFES-20
│   └── processed/                   # Dữ liệu đã làm sạch
│       ├── train/                   # Tập Train (~33k ảnh)
│       └── val/                     # Tập Validation (~8k ảnh)
│
├── 📄 prepare_dataset_local.py      # Kịch bản gộp dữ liệu
├── 📄 run.py                        # Khởi động nhanh app
├── 📄 requirements.txt              # Các thư viện Python cần thiết
└── 📄 README.md                     # File mô tả dự án này
```

---

## ⚙️ Quy trình Tiền xử lý (Preprocessing Pipeline)

Hệ thống sử dụng một chuỗi tiền xử lý hình ảnh phức tạp:

```
Ảnh đầu vào Raw (kích cỡ bất kỳ)
    ↓
1. Cắt vùng phân đoạn (YOLOv8n-seg)
   - Phát hiện và nhận diện khu vực tổn thương da
   - Xóa bỏ nền thừa xung quanh
    ↓
2. Tẩy lông (Thuật toán DullRazor)
   - Xóa bỏ chi tiết lông/tóc trên ảnh
   - Làm giảm hạt nhiễu
    ↓
3. Kiểm soát chất lượng
   - Đánh giá chất lượng ảnh chụp
   - Đảm bảo đúng độ phân giải
    ↓
4. Resize & Chuẩn hóa giá trị Pixel
   - Đổi kích thước thành 380x380
   - Đưa pixel về chuẩn [0-1]
    ↓
5. Chạy mô hình AI (EfficientNet-B4)
   - Trích xuất đặc trưng
   - Phân loại 24 lớp bệnh
    ↓
Đầu ra: Tên bệnh dự đoán + Tỉ lệ chính xác (Confidence)
```

---

## 🔬 Chi tiết Huấn luyện (Training)

### **Thành phần Bộ Dữ liệu**

| Nguồn Cấp | Số Lượng Ảnh | Số Lớp | Cách dùng |
|--------|--------|---------|-------|
| DermNet NZ | ~23k | 23 | Dùng để train phần lớn |
| ISIC 2019 | ~25k | 8 | Chuyên trị nhóm Ung thư Hắc tố |
| PAD-UFES-20 | ~2k | 6 | Bổ trợ thêm Metadata bệnh nhân |
| **Tổng cộng** | **~41k** | **24 (Đã gộp)** | **Kết hợp** |

### **Tỷ lệ Chia Data (Data Split)**

- **Tập Train (Huấn luyện)**: 80% (~33.000 ảnh)
- **Tập Validation (Kiểm định)**: 20% (~8.000 ảnh)
- **Phương pháp chia**: Chia theo Bệnh nhân (Ngăn rò rỉ dữ liệu - data leakage)
- **Mức tối thiểu mỗi nhóm bệnh**: Dành ít nhất 50 ảnh kiểm định cho mỗi nhóm

### **Cấu hình Huấn luyện**

```python
# Cấu hình AI
Kiến trúc: EfficientNet-B4 (PyTorch)
Trọng số khởi tạo: Trọng số gốc từ bài toán ImageNet

```

### **Nền tảng Train**

- **Nền tảng**: Hệ thống Máy chủ Kaggle Notebooks
- **Card Đồ họa (GPU)**: NVIDIA P100 (16GB VRAM)
- **Thời gian Train dài nhất**: ~10,4 tiếng
- **Môi trường**: PyTorch phiên bản 2.6+

**Phiên bản Tốt nhất:** V2.1 (86.2% độ xác thực val acc)  
---

## 📈 Lịch sử Phát triển các Phiên bản Model

- **V1.0 (`kaggle-train-24class-v1.0-results`)**: Phiên bản tinh chỉnh đầu tiên của EfficientNet-B4 trên tập dữ liệu 24 lớp. Đạt độ chính xác (validation accuracy) khoảng ~69% và điểm Macro F1 ~0.596. Đóng vai trò làm cột mốc cơ sở (baseline) cho dự án.
- **V2.0 (`kaggle-train-24class-v2.0-results`)**: Bản nâng cấp lớn. Cải thiện mạnh mẽ các bước tiền xử lý dữ liệu và áp dụng kỹ thuật làm phong phú hình ảnh (baseline augmentation). Đạt độ chính xác ~86% và điểm Macro F1 ~0.867, cho thấy sự nhảy vọt về hiệu năng, mặc dù bắt đầu xuất hiện những dấu hiệu sớm của hiện tượng quá khớp (overfitting).
- **V2.1 (`kaggle-train-24class-v2.1-results`)**: Bản tinh chỉnh của V2.0. Tích hợp thêm kỹ thuật MixUp augmentation và Micro learning rates để chống lại hiện tượng overfitting. Đạt **độ chính xác ~86.2%** và **điểm Macro F1 ~0.880** (Tốt nhất). Mô hình có khả năng tổng quát hóa (generalized) tốt hơn trên toàn bộ 24 loại bệnh.

---

## 🛠️ Cài đặt Phát triển

### Cài đặt thủ công (Không dùng Docker)

```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Linux/Mac)
source .venv/bin/activate  
# Nếu ở Windows thì dùng lệnh: .venv\Scripts\activate

# Cài đặt thư viện Python
pip install -r requirements.txt

# Chạy Backend server
cd backend
uvicorn app.main:app --reload --port 8000

# Chạy Frontend web (Mở bằng một Terminal/Cmd mới)
cd frontend
python -m http.server 8080
```

---

## ⚠️ Tuyên bố Từ chối Trách nhiệm (Disclaimer)

**Dự án chỉ nhằm mục đích nghiên cứu và giáo dục.**  
Tất cả các chẩn đoán từ hệ thống AI chỉ mang tính chất **tham khảo chuyên gia** và **không thay thế cho việc chẩn đoán y tế lâm sàng của bác sĩ chuyên khoa**.  
Vui lòng luôn nhờ tới các chuyên gia da liễu có chứng chỉ để được tư vấn khi phát hiện bệnh!

---