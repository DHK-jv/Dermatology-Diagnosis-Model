# 🚀 Infrastructure Configuration

**Folder chứa cấu hình để deploy MedAI Dermatology**

---

## 📁 Cấu Trúc

```
infrastructure/
├── nginx/
│   └── nginx.conf          # Cấu hình Nginx (Gateway)
├── docker-compose.yml      # File "thần thánh" - Bật cả web, API, DB
└── .env                    # Environment variables
```

---

## 🐳 Quick Start với Docker

```bash
cd infrastructure

# 1. Copy model file trước
cp ../models/efficientnet_b3_derma_finetuned.keras ../backend/ml_models/

# 2. Start tất cả services (MongoDB + Backend + Nginx)
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f

# 5. Stop services  
docker-compose down
```

---

## 📝 Files Giải Thích

### `nginx.conf`
Nginx làm Gateway:
- Serve frontend static files (HTML/CSS/JS)
- Reverse proxy `/api/*` requests → Backend API (port 8000)
- Load balancing (future)

### `docker-compose.yml`
Orchestrate 3 services:
1. **MongoDB** - Database (port 27017)
2. **Backend** - FastAPI API (port 8000) 
3. **Nginx** - Web server + Gateway (port 80)

### `.env`
Environment variables:
- MongoDB connection string
- API ports
- Model paths
- Security configs

---

## 🔧 Configuration

### MongoDB
```bash
# Default connection
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=medai_dermatology
```

### Backend
```bash
BACKEND_PORT=8000
MODEL_PATH=backend/ml_models/efficientnet_b3_derma_finetuned.keras
```

---

## 🌐 Access URLs

Sau khi `docker-compose up -d`:

- **Frontend**: http://localhost
- **Backend API Docs**: http://localhost:8000/docs
- **MongoDB**: localhost:27017 (internal)

---

## 🛠️ Troubleshooting

### Port đã được sử dụng
```bash
# Check ports
sudo lsof -i :80
sudo lsof -i :8000
sudo lsof -i :27017

# Kill process nếu cần
sudo kill -9 <PID>
```

### Xem logs
```bash
docker-compose logs backend
docker-compose logs nginx
docker-compose logs mongodb
```

### Restart service
```bash
docker-compose restart backend
docker-compose restart nginx
```

---

## 📚 Khi Nào Dùng

**Hiện tại:** Dự án đang ở giai đoạn training, infrastructure chưa cần thiết.

**Sau này:** Khi đã train xong model và muốn:
- Deploy production
- Test với web interface
- Demo cho stakeholders

---

## ⚠️ Note

Folder này chứa **cấu hình infrastructure** cho giai đoạn deployment. Hiện tại tập trung vào:
1. ✅ Tiền xử lý data
2. ✅ Training model trên Kaggle
3. ⏳ Deploy (giai đoạn sau)
