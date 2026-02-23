# 🏥 MedAI Dermatology - AI Chẩn Đoán Bệnh Da Liễu

> **Tác giả:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Hệ thống Phân loại Bệnh Da liễu dựa trên Deep Learning**

---

## 📊 Tổng quan

Một hệ thống AI chẩn đoán bệnh da liễu sử dụng các kỹ thuật học sâu (deep learning) và xử lý ảnh y tế tiên tiến. Hệ thống tích hợp các luồng tiền xử lý (preprocessing) chuyên nghiệp và mô hình mạng nơ-ron hiện đại để hỗ trợ các bác sĩ trong việc chẩn đoán.

**Các thành tựu chính:**
- ✅ **Bộ dữ liệu (Dataset):** ~41.000 ảnh (DermNet NZ + ISIC 2019 + PAD-UFES-20)
- ✅ **Tiền xử lý (Preprocessing):** Luồng tự động (Cắt phân đoạn bằng YOLOv8 + Xóa lông + Kiểm soát chất lượng)
- ✅ **Mô hình (Model):** EfficientNet-B4 V2.1 (Độ chính xác được xác thực với validation accuracy đạt 86,2%, F1 0,880)
- ✅ **Hệ thống:** Ứng dụng Full-stack với backend dùng FastAPI và frontend web
- ✅ **Phân loại:** 24 loại bệnh da liễu

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

1. **Tải xuống:** `efficientnet_b4_derma_v2_1_finetuned.pth` (71MB)
    Link drive: https://drive.google.com/file/d/1O4QKvJgp8FxHhzz8KSM-Gs0xv3aR57-y/view?usp=drive_link
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
│   │   │   ├── gradcam.py           # Giải mã quyết định (Heatmap)
│   │   │   ├── inference.py         # Chạy AI suy luận
│   │   │   ├── preprocessing.py     # Tiền xử lý ảnh
│   │   │   ├── security.py          # Bảo mật JWT, Hashing
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
│   │   ├── admin.js                 # Quản trị viên Dashboard
│   │   ├── api.js                   # Kết nối API Backend
│   │   ├── app.js                   # Logic app chính
│   │   ├── auth.js                  # Cơ chế đăng nhập/đăng ký
│   │   ├── config.js                # Cấu hình biến Web
│   │   ├── diagnose.js              # Luồng giao diện lúc chẩn đoán
│   │   ├── history.js               # Logic trang lịch sử
│   │   ├── medical-terms.js         # File từ vựng dịch từ Anh sang Việt
│   │   ├── result.js                # Luồng in kết quả
│   │   └── utils.js                 # Hàm tiện ích chung
│   ├── pages/                       # Các trang HTML
│   │   ├── admin.html               # Bảng bảng Dashboard Admin
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
│   │   ├── kaggle-train.ipynb       # Notebook train chính trên Kaggle
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

### Cài đặt tự động (Khuyến nghị dùng Docker & Nginx)

Hệ thống cung cấp sẵn file `docker-compose.yml` giúp bạn triển khai toàn bộ dự án chỉ với một dòng lệnh, không cần lo lắng về việc cài đặt môi trường hay xung đột thư viện.

**1. Vai trò của Docker và Nginx trong hệ thống:**
- **Docker**: Đóng gói toàn bộ mã nguồn, các thư viện phức tạp (như PyTorch, FastAPI) thành các "container" độc lập. Việc này giúp dự án chạy ổn định và nhất quán trên mọi máy tính (Windows, Mac, Linux) y hệt như trên máy chủ phát triển mà không làm rác máy thật của bạn.
- **Nginx**: Đóng vai trò là Web Server và Proxy ngược (Reverse Proxy).
  - Tối ưu hóa truy xuất và bộ đệm (cache) cực nhanh cho các file giao diện tĩnh (HTML, CSS, JS).
  - Định tuyến thông minh: Nginx sẽ hứng toàn bộ request. Nếu người dùng mở trang web, nó trả về giao diện Frontend. Nếu giao diện gọi nạp dữ liệu (`/api/*`), Nginx sẽ âm thầm chuyển tiếp lệnh đó sang Backend FastAPI đang chạy ngầm trên cổng 8000. Cơ chế này giúp xóa bỏ hoàn toàn lỗi bảo mật CORS (Cross-Origin) và quản lý luồng dữ liệu một cửa chuyên nghiệp như các hệ thống thực tế ngoài doanh nghiệp.

**2. Cách khởi chạy:**

Yêu cầu máy tính của bạn đã cài đặt sẵn [Docker Desktop](https://www.docker.com/products/docker-desktop/) (hoặc Docker Engine).

```bash
# 1. Tải về và biên dịch toàn bộ hệ thống lên (chạy ngầm)
docker compose up -d --build

# 2. Xem tiến trình log để biết khi nào Backend tải mượt mà mô hình AI xong (Bấm Ctrl+C để thoát xem logs)
docker compose logs -f backend
```

Ứng dụng sẽ tự động hợp nhất và chạy tại một cổng duy nhất: **http://localhost** (cổng 80 mặc định). Bạn không cần phải mở 2 terminal như khi chạy thủ công.

*Lệnh hỗ trợ dọn dẹp:*
```bash
# Tắt hệ thống
docker compose down
```

---

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