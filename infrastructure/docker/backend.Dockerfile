# ============================================================
# Backend Dockerfile - FastAPI + PyTorch + EfficientNet-B4
# Build context: . (Project Root) - see docker-compose.yml
# ============================================================
FROM python:3.11-slim

LABEL maintainer="Duong Hoang Khang"
LABEL description="MedAI Dermatology - FastAPI Backend"

# Set working directory
WORKDIR /app

# ── System dependencies ──────────────────────────────────────
# libgl1: OpenCV needs this for image processing
# libglib2.0-0: Required by OpenCV
# libgomp1: PyTorch needs OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
# Note: paths are relative to build context (.)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt \
        --extra-index-url https://download.pytorch.org/whl/cpu

# ── Application code ──────────────────────────────────────────
# Copy backend app code
COPY backend/app/ ./app/

# Copy shared preprocessing module (CRITICAL fix)
COPY preprocessing/ ./preprocessing/

# ── Model weights (mounted as volume at runtime) ──────────────
# Create directory - actual .pth file mounted via docker-compose volume
RUN mkdir -p ml_models uploads

# ── Environment variables ─────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONPATH=/app

# ── Health check ──────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Expose port ───────────────────────────────────────────────
EXPOSE 8000

# ── Start server ──────────────────────────────────────────────
CMD ["python", "-m", "uvicorn", "app.main:app", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "1", "--log-level", "info"]
