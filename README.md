# 🏥 MedAI Dermatology - AI Chẩn Đoán Bệnh Da Liễu

> **Tác giả:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Hệ thống Phân loại Bệnh Da liễu dựa trên Deep Learning**

---

## PHẦN MỞ ĐẦU

### 1. Tính cấp thiết và Giới thiệu tổng quan
Một hệ thống AI chẩn đoán bệnh da liễu sử dụng các kỹ thuật học sâu (deep learning) và xử lý ảnh y tế tiên tiến. Hệ thống tích hợp các luồng tiền xử lý (preprocessing) chuyên nghiệp và mô hình mạng nơ-ron hiện đại để hỗ trợ các bác sĩ trong việc chẩn đoán, giảm thiểu sai sót và tăng tốc độ chẩn đoán ban đầu.

### 2. Mục tiêu và Những đóng góp của dự án
- ✅ **Bộ dữ liệu (Dataset):** Xây dựng tập dữ liệu ~41.000 ảnh (DermNet NZ + ISIC 2019 + PAD-UFES-20).
- ✅ **Tiền xử lý (Preprocessing):** Xây dựng luồng tự động (Cắt phân đoạn bằng YOLOv8 + Xóa lông + Kiểm soát chất lượng).
- ✅ **Mô hình (Model):** Tối ưu hóa mô hình EfficientNet-B4 V2.1 (Độ chính xác được xác thực với validation accuracy đạt 86,2%, F1 0,880).
- ✅ **Hệ thống:** Phát triển Web App Full-stack với backend dùng FastAPI và frontend web để đưa mô hình vào ứng dụng thực tế.
- ✅ **Khả năng Phân loại:** Hỗ trợ chẩn đoán chính xác 24 loại bệnh da liễu.

---

## CHƯƠNG 1: TỔNG QUAN VỀ CHẨN ĐOÁN BỆNH DA LIỄU VỚI HỌC SÂU

### 1.1 Bài toán phân loại bệnh da liễu
Danh sách 24 nhóm bệnh lý về da liễu được hệ thống hỗ trợ phân lớp và chẩn đoán:

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

## CHƯƠNG 2: PHƯƠNG PHÁP VÀ KIẾN TRÚC HỆ THỐNG ĐỀ XUẤT

### 2.1 Cấu trúc và các thành phần của hệ thống
Hệ thống được thiết kế theo kiến trúc Microservices cơ bản, quản lý riêng biệt phần AI, Backend, Frontend:

```text
MedAI_Dermatology/
│
├── 📂 backend/                      # Hệ thống Backend API (FastAPI)
│   ├── app/
│   │   ├── services/                # Logic chính (inference.py, preprocessing.py, gradcam.py)
│   ├── ml_models/                   # Chứa trọng số AI (efficientnet, yolov8)
│
├── 📂 frontend/                     # Giao diện Web (HTML/CSS/JS)
│   ├── js/                          # Logic hiển thị và kết nối API 
│   ├── pages/                       # Bố cục giao diện Dashboard, Diagnose
│
├── 📂 preprocessing/                # Mã nguồn tiền xử lý luồng hỗn hợp
├── 📂 research/                     # Sổ tay Jupyter huấn luyện AI
└── 📂 data/                         # Dữ liệu ảnh thô và đã xử lý
```

### 2.2 Quy trình Tiền xử lý (Preprocessing Pipeline)
Hệ thống đề xuất sử dụng một chuỗi tiền xử lý hình ảnh phức tạp để tối ưu hóa đặc trưng trước khi đưa vào mô hình học sâu:

```text
Ảnh đầu vào Raw (kích cỡ bất kỳ)
    ↓
1. Cắt vùng phân đoạn (YOLOv8n-seg): Nhận diện tổn thương da, xóa nền dư thừa.
    ↓
2. Tẩy lông (Thuật toán DullRazor): Xóa bỏ chi tiết lông/tóc, giảm nhiễu.
    ↓
3. Kiểm soát chất lượng ảnh.
    ↓
4. Resize (380x380) & Chuẩn hóa giá trị Pixel về [0-1].
    ↓
5. Chạy mô hình phân lớp (EfficientNet-B4): Trích xuất đặc trưng và dự đoán.
```

### 2.3 Mô hình học sâu (Deep Learning Model)
- **Kiến trúc**: Lựa chọn EfficientNet-B4 (PyTorch) kết hợp kỹ thuật tăng cường dữ liệu.
- **Tối ưu hóa**: Áp dụng MixUp augmentation và Micro learning rates để giảm thiểu Overfitting trên tập dữ liệu y tế.

---

## CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM

### 3.1 Bộ dữ liệu sử dụng
- **Kích thước**: ~41.000 ảnh từ các nguồn mở (DermNet NZ, ISIC 2019, PAD-UFES-20).
- **Tỷ lệ chia data**: 80% Train / 20% Validation. Chia theo ID bệnh nhân để tránh rò rỉ dữ liệu (Data Leakage).

### 3.2 Thiết lập huấn luyện
- **Phần cứng**: Thực nghiệm trên môi trường Kaggle Notebooks với GPU NVIDIA P100 - 16GB VRAM.

### 3.3 Kết quả các phiên bản thực nghiệm
- **V1.0 (`kaggle-train-24class-v1.0-results`)**: Cột mốc baseline. Đạt độ chính xác khoảng ~69%, Macro F1 ~0.596.
- **V2.0 (`kaggle-train-24class-v2.0-results`)**: Cải tiến tiền xử lý và baseline augmentation. Đạt độ chính xác ~86%, Macro F1 ~0.867.
- **V2.1 (`kaggle-train-24class-v2.1-results` - Tốt nhất)**: Tích hợp thêm MixUp và Micro LR. Đạt **độ chính xác ~86.2%** và **điểm Macro F1 ~0.880**. Khả năng tổng quát hóa trên 24 loại bệnh đạt mức tối ưu.

---

## CHƯƠNG 4: KẾT LUẬN VÀ HƯỚNG DẪN CÀI ĐẶT

### 4.1 Kết luận
Dự án đã phát triển thành công một hệ thống khép kín từ khâu tiền xử lý, huấn luyện mô hình học sâu cho tới giao diện tích hợp người dùng, cho phép chẩn đoán 24 bệnh lý da liễu với độ chính xác cao.

### 4.2 Hướng dẫn cài đặt phát triển
Trọng số của mô hình (Model weights) **không được kèm theo** (do kích thước quá lớn). Cần tải: `efficientnet_b4_derma_v2_1_finetuned.pth` (71MB) từ [Drive](https://drive.google.com/file/d/1O4QKvJgp8FxHhzz8KSM-Gs0xv3aR57-y/view?usp=drive_link) và bỏ vào `backend/ml_models/`.

**Chạy với Docker:**
```bash
git clone https://github.com/DHK-jv/Dermatology-Diagnosis-Model.git
cd Dermatology-Diagnosis-Model
docker compose up -d --build
```

**Chạy thủ công:**
```bash
# Terminal 1: Chạy Backend (FastAPI)
cd backend && uvicorn app.main:app --reload --port 8000
# Terminal 2: Chạy Frontend
cd frontend && python -m http.server 8080
```
Truy cập tại: `http://localhost:8080`

### 4.3 Tuyên bố Từ chối Trách nhiệm (Disclaimer)
**Dự án chỉ nhằm mục đích nghiên cứu và giáo dục.** Tất cả các chẩn đoán từ hệ thống AI chỉ mang tính chất **tham khảo chuyên gia** và không thay thế cho y tế lâm sàng.