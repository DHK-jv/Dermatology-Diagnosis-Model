# ============================================================
# Frontend Dockerfile - Nginx serving static files
# Build context: ./frontend  (docker-compose sets this)
# nginx.conf được copy từ ../infrastructure/nginx/nginx_docker.conf
# ============================================================
FROM nginx:alpine

LABEL maintainer="Duong Hoang Khang"
LABEL description="MedAI Dermatology - Frontend (Nginx)"

# Copy frontend static files vào nginx html root
COPY . /usr/share/nginx/html/

# Xóa Dockerfile khỏi html root nếu có
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/.dockerignore \
    /usr/share/nginx/html/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
