# ============================================================
# Frontend Dockerfile - Nginx serving static files
# ============================================================
FROM nginx:alpine

LABEL maintainer="Duong Hoang Khang"
LABEL description="MedAI Dermatology - Frontend (Nginx)"

# Copy frontend files
COPY . /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
