# HƯỚNG DẪN SỬ DỤNG VÀ CÀI ĐẶT
**Dự án: MedAI Dermatology - AI Chẩn Đoán Bệnh Da Liễu**

---

## 📌 Truy Cập Hệ Thống

Hệ thống MedAI Dermatology đang hoạt động tại:

| Thành phần | Địa chỉ | Ghi chú |
|---|---|---|
| **Giao diện Web** | [https://khangjv.id.vn](https://khangjv.id.vn) | Frontend trên VPS |
| **Backend API** | [https://hoangkhang2-medai-dermatology.hf.space](https://hoangkhang2-medai-dermatology.hf.space) | Hugging Face Spaces |
| **API Docs (Swagger)** | [https://hoangkhang2-medai-dermatology.hf.space/docs](https://hoangkhang2-medai-dermatology.hf.space/docs) | Dành cho lập trình viên |

---

## 1. Kiến Trúc Triển Khai Hiện Tại

```
Người dùng ──► https://khangjv.id.vn (VPS - Frontend)
                        │
                        │ Gọi API
                        ▼
              https://hoangkhang2-medai-dermatology.hf.space (Hugging Face - Backend + AI)
                        │
                        ▼
                    MongoDB Atlas (Lưu lịch sử chẩn đoán)
```

- **Frontend** (HTML/CSS/JS): Được host trực tiếp trên VPS nội địa qua File Manager.
- **Backend** (FastAPI + EfficientNet-B4): Đóng gói bằng Docker và chạy trên Hugging Face Spaces (cổng 7860).
- **Database**: MongoDB Atlas (Cloud), kết nối qua biến môi trường trên HF Spaces.

---

## 2. Yêu Cầu Hệ Thống (Dành Cho Lập Trình Viên)

Chỉ cần thiết nếu bạn muốn chạy nội bộ (local) để debug hoặc phát triển:

- Hệ điều hành: Linux/Windows/macOS
- Python: >= 3.10
- Docker (nếu test bằng Docker)
- RAM: tối thiểu 8GB
- GPU: không bắt buộc (mô hình có thể suy luận bằng CPU)

---

## 3. Chuẩn Bị Mô Hình (Weights)

Các file trọng số AI đã có sẵn trong repository tại `backend/ml_models/`:

| File | Mô tả |
|---|---|
| `efficientnet_b4_derma_v3_0.pth` | Mô hình phân loại chính (24 bệnh) |
| `yolov8n-seg.pt` | Mô hình phân đoạn vùng tổn thương |

Không cần tải thêm từ nguồn bên ngoài.

---

## 4. Cài Đặt Và Chạy Nội Bộ (Local)

### 4.1. Chạy bằng Docker (Khuyến nghị)
```bash
# Build image
docker build -t medai-hf .

# Chạy container
docker run -p 7860:7860 medai-hf
```
Truy cập: `http://localhost:7860`

### 4.2. Chạy thủ công (Không Docker)

**Terminal 1 - Backend:**
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate          # Windows

pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```
Backend chạy tại: `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 3000
```
Frontend chạy tại: `http://localhost:3000`

---

## 5. Triển Khai Lên Production

### 5.1. Backend → Hugging Face Spaces
1. Upload các thư mục sau lên HF Space `hoangkhang2/MedAI_Dermatology`:
   - `Dockerfile` (file gốc ở thư mục root)
   - `backend/` (toàn bộ code + ml_models)
   - `preprocessing/` (pipeline AI)
2. Vào **Settings → Variables and secrets**, thêm:
   - `MONGODB_URL` = connection string MongoDB Atlas
   - `USE_MONGODB` = `true`
   - `MONGODB_DB_NAME` = `medai_dermatology`
   - `ALLOWED_ORIGINS` = `https://khangjv.id.vn,https://www.khangjv.id.vn`

### 5.2. Frontend → VPS (khangjv.id.vn)
1. Upload toàn bộ nội dung thư mục `frontend/` lên `public_html/` qua File Manager.
2. File `frontend/js/runtime-env.js` đã được cấu hình sẵn URL backend HF Spaces.
3. Cấu trúc trên hosting:
   ```
   public_html/
   ├── index.html
   ├── admin.html
   ├── css/
   ├── js/
   │   ├── config.js
   │   ├── runtime-env.js
   │   └── ...
   └── pages/
   ```

---

## 6. Sử Dụng Hệ Thống

### 6.1. Chẩn Đoán Bệnh Da Liễu
1. Truy cập [https://khangjv.id.vn](https://khangjv.id.vn).
2. Nhấn **"Bắt đầu chẩn đoán"** → Upload ảnh da liễu (chụp rõ nét, ánh sáng tốt, trực diện vùng tổn thương).
3. Nhấn **"Phân tích AI"** → Hệ thống sẽ:
   - Cắt nền bằng YOLOv8
   - Tẩy lông bằng DullRazor
   - Dự đoán bằng EfficientNet-B4
4. Xem kết quả: Tên bệnh, Độ tin cậy (%), Mức độ nguy hiểm, Bản đồ nhiệt Grad-CAM.

### 6.2. Xem Lịch Sử
- Vào trang **Lịch sử** để xem lại tất cả các lần chẩn đoán trước đó.

### 6.3. Phản Hồi Chuyên Môn
- Bác sĩ/Admin có thể nhấn **"Đúng/Sai"** tại trang kết quả để đánh giá độ chính xác, giúp cải thiện mô hình.

### 6.4. Dashboard Admin
- Đăng nhập với tài khoản quản trị để xem thống kê: biểu đồ ca chẩn đoán theo thời gian, tần suất từng loại bệnh.
