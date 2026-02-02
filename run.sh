#!/bin/bash

# MedAI Dermatology - Master Launch Script
# Tác dụng: Chạy song song cả Backend và Frontend cùng lúc

# Màu sắc cho đẹp
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}   MedAI Dermatology Diagnosis System      ${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""

# 1. Hàm dọn dẹp (Tắt Backend khi tắt script)
cleanup() {
    echo ""
    echo -e "${RED}🛑 Đang dừng hệ thống...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID
        echo "   - Đã tắt Backend (PID: $BACKEND_PID)"
    fi
    echo -e "${GREEN}👋 Tạm biệt!${NC}"
    exit
}

# Bắt sự kiện Ctrl+C để chạy hàm cleanup
trap cleanup INT

# 2. Khởi động Backend
if [ -f "backend/start_backend.sh" ]; then
    echo -e "${GREEN}🚀 [1/2] Đang khởi động Backend Server...${NC}"
    chmod +x backend/start_backend.sh
    
    # Chạy Backend ở chế độ nền (dấu &)
    # Lưu ý: Không ẩn log hoàn toàn để user thấy nếu đang cài thư viện
    cd backend
    ./start_backend.sh &
    BACKEND_PID=$! # Lưu lại ID của tiến trình Backend để sau này tắt
    cd ..
    
    echo "   ✅ Backend đang chạy ngầm (PID: $BACKEND_PID)"
    echo "   ⏳ Đợi 5 giây để Backend ổn định..."
    sleep 5
else
    echo -e "${RED}❌ Lỗi: Không tìm thấy backend/start_backend.sh${NC}"
    exit 1
fi

# 3. Khởi động Frontend
if [ -f "frontend/start_frontend.sh" ]; then
    echo -e "${GREEN}🌐 [2/2] Đang khởi động Frontend Server...${NC}"
    chmod +x frontend/start_frontend.sh
    
    cd frontend
    # Chạy Frontend ở chế độ foreground (để giữ cửa sổ terminal không bị tắt)
    # Thêm wait để đảm bảo Ctrl+C bắt được tín hiệu đúng
    ./start_frontend.sh
else
    echo -e "${RED}❌ Lỗi: Không tìm thấy frontend/start_frontend.sh${NC}"
    # Nếu lỗi frontend thì nhớ tắt backend đã chạy trước đó
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    exit 1
fi
