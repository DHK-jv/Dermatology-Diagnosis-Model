# Hướng Dẫn Triển Khai Hệ Thống (Production)

Gói này được thiết kế để triển khai hệ thống MedAI Dermatology lên **Hugging Face Spaces** (Backend) và **VPS khangjv.id.vn** (Frontend).

## 1. Triển khai Backend (Hugging Face Spaces)

1. Tạo một **New Space** trên Hugging Face.
2. Chọn SDK: **Docker** (Blank).
3. Tại tab **Files and versions**, upload toàn bộ nội dung trong thư mục này (bao gồm `Dockerfile`, `backend/`, `preprocessing/`, `frontend/`).
4. **CẤU HÌNH BIẾN MÔI TRƯỜNG (QUAN TRỌNG):**
   Vào tab **Settings** -> **Variables and Secrets**:
   - Thêm Secret `MONGODB_URL`: Điền chuỗi kết nối Atlas của bạn (ví dụ: `mongodb+srv://...`).
   - Thêm Variable `USE_MONGODB`: `true`.
   - Thêm Variable `MONGODB_DB_NAME`: `medai_dermatology`.
   - Thêm Variable `MODEL_REQUIRED`: `true`.
5. Nhấn **Factory Reboot** để hệ thống bắt đầu build và chạy.

## 2. Triển khai Frontend (VPS khangjv.id.vn)

1. Copy toàn bộ thư mục `frontend/` (đã được tôi cấu hình sẵn trong gói này) lên thư mục web của VPS.
2. **Lưu ý:** File `js/config.js` trong gói này đã được tôi "khóa cứng" địa chỉ gọi về Hugging Face. Bạn sẽ không bao giờ bị lỗi "gọi nhầm local" như trước nữa.
3. Cấu hình Nginx trỏ vào thư mục này.

## 3. Kiểm tra kết nối
- Truy cập `https://khangjv.id.vn`.
- Mở F12 Console, bạn sẽ thấy dòng: `[Config] Environment: Production (External) -> https://hoangkhang2-medai-dermatology.hf.space`.
- Đăng nhập và xem Lịch sử sẽ hoạt động mượt mà.

---
**MedAI Engineering Team**
