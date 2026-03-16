# System Architecture (Local vs Production)

This project supports two explicit modes. The frontend chooses the API endpoint at runtime.

**Local Development (Nginx Reverse Proxy)**
Flow: `http://localhost` → Nginx → local frontend + local backend + model + preprocessing.

Key points:
- Nginx serves the static frontend and proxies `/api/v1/` and `/uploads/` to the local backend.
- Frontend uses a relative API base URL so all calls go through Nginx.
- Backend runs locally and loads the AI model and preprocessing pipeline.

Run (Docker, recommended):
```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

**Production (Frontend Only)**
Flow: `https://khangjv.id.vn` → frontend only → Render backend API.

Key points:
- This server does **not** run the backend or model.
- Frontend calls the Render API directly: `https://dermatology-diagnosis-model.onrender.com`.

Run (Docker, frontend-only):
```bash
docker compose -f infrastructure/docker-compose.prod.yml up -d --build
```

**Runtime API Base URL**
The frontend reads a runtime override first:
- `window.__API_BASE_URL__` from `frontend/js/runtime-env.js`
- Then auto-detects based on hostname/port if no override is set.

Docker injects the runtime override at container startup using `API_BASE_URL`.

**Nginx Configs**
- Local Docker Nginx: `infrastructure/nginx/nginx_docker.conf`
- Local Host Nginx: `infrastructure/nginx/medai_nginx.conf`
- Production (frontend-only, host Nginx): `infrastructure/nginx/vps_production.conf`
- Production (frontend-only, docker Nginx): `infrastructure/nginx/nginx_frontend_only.conf`
