# ============================================================
# Backend-only Dockerfile for Hugging Face Spaces
# Serves ONLY the FastAPI API (no frontend static files)
# Frontend is served from VPS (khangjv.id.vn) via Nginx
# ============================================================
FROM python:3.11-slim

LABEL maintainer="Duong Hoang Khang"
LABEL description="MedAI Dermatology - Backend API for Hugging Face"

WORKDIR /app

# ── System dependencies ──────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt \
        --extra-index-url https://download.pytorch.org/whl/cpu

# ── Application code ──────────────────────────────────────────
COPY backend/app/ ./app/
COPY preprocessing/ ./preprocessing/
COPY backend/ml_models/ ./ml_models/
COPY frontend/ ./frontend/

RUN mkdir -p uploads && chmod 777 uploads && chmod 777 /app

# ── Environment variables ─────────────────────────────────────
# MONGODB_URL, USE_MONGODB, MONGODB_DB_NAME must be set in HF Spaces Settings -> Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    PYTHONPATH=/app \
    MODEL_PATH=/app/ml_models/efficientnet_b4_derma_v3_0.pth \
    PREPROCESSING_MODE=auto \
    TORCH_THREADS=1

# Allow CORS from the VPS frontend domain
ENV ALLOWED_ORIGINS="https://khangjv.id.vn,https://www.khangjv.id.vn"

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "app.main:app", \
    "--host", "0.0.0.0", "--port", "7860", \
    "--workers", "1"]
