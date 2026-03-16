# ============================================================
# Frontend Dockerfile - Nginx serving static files
# Build context: ./frontend  (docker-compose sets this)
# nginx.conf được copy từ ../infrastructure/nginx/nginx_docker.conf
# ============================================================
FROM nginx:alpine

LABEL maintainer="Duong Hoang Khang"
LABEL description="MedAI Dermatology - Frontend (Nginx)"

# Install curl for reliable healthchecks + envsubst for runtime config
RUN apk add --no-cache curl gettext

# Copy frontend static files vào nginx html root
COPY frontend/ /usr/share/nginx/html/

# Xóa Dockerfile khỏi html root nếu có
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/.dockerignore \
    /usr/share/nginx/html/nginx.conf

# Runtime API base URL injection
COPY infrastructure/docker/frontend-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV API_BASE_URL=""

EXPOSE 80

# Render runtime env then start nginx
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

# Use curl for healthcheck (wget can be flaky or missing parameters in strict Alpine)
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost/ || exit 1
