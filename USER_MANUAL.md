# HƯỚNG DẪN SỬ DỤNG VÀ CÀI ĐẶT
**Dự án: MedAI Dermatology - AI Chẩn Đoán Bệnh Da Liễu**

---

Tài liệu này hướng dẫn cách cài đặt, cấu hình và sử dụng hệ thống MedAI Dermatology trên môi trường cục bộ (Local) hoặc thông qua Docker.

## 1. Yêu cầu Hệ thống
- Hệ điều hành: Linux/Windows/macOS
- Python: Phiên bản >= 3.10
- Docker (nếu triển khai bằng Docker Compose)
- Dung lượng RAM khuyến nghị: tối thiểu 8GB
- Không bắt buộc có GPU trên môi trường chạy server (vì mô hình có thể suy luận bằng CPU)

## 2. Chuẩn bị Mô hình (Weights)
Hệ thống sử dụng mô hình AI được tinh chỉnh từ EfficientNet-B4. Do kích thước tệp lớn (khoảng 71MB), trọng số (weights) không được đính kèm trong repository. Bạn cần tải file này trước khi khởi động dự án:

1. **Tải tệp trọng số**: `efficientnet_b4_derma_v2_1_finetuned.pth`
   - [Đường dẫn Google Drive](https://drive.google.com/file/d/1O4QKvJgp8FxHhzz8KSM-Gs0xv3aR57-y/view?usp=drive_link)
2. **Vị trí thư mục**: Đặt tệp tin vừa tải về theo đường dẫn chính xác như sau:
   `backend/ml_models/efficientnet_b4_derma_v2_1_finetuned.pth`

*(Ghi chú: File YOLOv8-seg.pt dùng để cắt ảnh đã tự động được hệ thống cấu hình sẵn).*

---

## 3. Cài đặt bằng Docker (Giải pháp khuyên dùng)

### 3.1. Local Development (Nginx Reverse Proxy)
Tất cả Frontend, Backend, AI model và preprocessing chạy cục bộ. Nginx proxy `/api/v1/` về backend.

1. Đảm bảo bạn đã cài đặt Docker và Docker Compose.
2. Mở Terminal tại thư mục gốc dự án `MedAI_Dermatology`.
3. Chạy lệnh:
   ```bash
   docker compose -f infrastructure/docker-compose.yml up -d --build
   ```
4. Đợi quá trình build hoàn tất (khoảng 2-5 phút).
5. Truy cập: `http://localhost`.

### 3.2. Production (Frontend Only)
Chỉ triển khai frontend. Backend chạy trên Render và frontend gọi trực tiếp API Render.

1. Trên VPS/Server production, chạy:
   ```bash
   docker compose -f infrastructure/docker-compose.prod.yml up -d --build
   ```
2. Nginx production sử dụng `infrastructure/nginx/vps_production.conf`.
3. Truy cập: `https://khangjv.id.vn`.

---

## 4. Cài đặt chạy nội bộ (Local/Thủ công)
Nếu bạn muốn cài trực tiếp trên máy để dễ dàng chỉnh sửa hoặc debug source code, hãy làm theo các bước sau:

### Bước 4.1. Tạo môi trường ảo và Cài đặt thư viện
```bash
# Mở terminal tại thư mục gốc dự án
python -m venv venv

# Kích hoạt môi trường (Windows)
venv\Scripts\activate
# Kích hoạt môi trường (Linux/Mac)
source venv/bin/activate

# Cài đặt toàn bộ thư viện cần thiết
pip install -r requirements.txt
```

### Bước 4.2. Khởi chạy Backend (FastAPI)
```bash
# Đứng từ thư mục gốc, di chuyển vào thư mục backend
cd backend

# Chạy server Uvicorn (Cổng mặc định 8000)
uvicorn app.main:app --reload --port 8000
```
Server Backend sẽ chạy tại `http://localhost:8000`. Cung cấp kho API cho hệ thống.
Tài liệu Swagger API (dành cho lập trình viên) nằm tại: `http://localhost:8000/docs`.

### Bước 4.3. Khởi chạy Frontend
(Mở thêm một cửa sổ Terminal mới, nhớ giữ backend đang chạy)
```bash
# Chuyển tới thư mục frontend
cd frontend

# Dựng server tĩnh bằng công cụ có sẵn của Python
python -m http.server 8080
```
Ứng dụng Web sẽ mở trên trình duyệt tại cổng 8080: `http://localhost:8080`.

### Bước 4.4. (Tuỳ chọn) Chạy qua Nginx Local
Nếu muốn đúng kiến trúc local (Nginx reverse proxy), dùng cấu hình:
`infrastructure/nginx/medai_nginx.conf` và truy cập `http://localhost`.

---

## 5. Sử dụng Hệ thống
1. **Truy cập Trang chủ**: Tại giao diện chính, người dùng sẽ đọc thể lệ và các từ chối trách nhiệm về tính y sinh của ứng dụng.
2. **Chẩn đoán (Diagnose)**:
   - Tải lên (Upload) bức ảnh da liễu cần chẩn đoán. Khuyến khích chụp trực diện, rõ nét, khu vực có ánh sáng tốt.
   - Nhấn "Phân tích AI". Hệ thống sẽ xử lý qua luồng tiền xử lý (Cắt ảnh YOLO, Tẩy lông DullRazor) và dự đoán bằng EfficientNet.
   - Kết quả trả về gồm: Tên bệnh, Độ tin cậy (Confidence), độ nguy hiểm của bệnh, và một hình ảnh "Bản đồ Nhiệt (Grad-CAM)" để giải thích vùng da AI đang tập trung quan sát.
3. **Lịch sử**: Kiểm tra lại toàn bộ ảnh đã từng được chẩn đoán.
4. **Dashboard Admin**: (Nếu có tài khoản quản trị). Truy cập để xem các số liệu thống kê về tần suất phát sinh các ca chẩn đoán ung thư, biểu đồ theo tuần/tháng.
