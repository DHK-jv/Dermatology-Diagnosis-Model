/**
 * Cấu hình API
 * Cấu hình tập trung cho các endpoint API
 */

const API_CONFIG = {
    // URL cơ sở cho Backend API
    // - Docker/Nginx (port 80/8080): chuỗi rỗng → nginx sẽ proxy /api/ tới backend
    // - Chạy local (DEV) qua run.py (port 3000): gọi trực tiếp tới localhost:8000
    BASE_URL: (() => {
        const explicitBaseUrl =
            (typeof window !== 'undefined' && window.__API_BASE_URL__) ||
            document.querySelector('meta[name="api-base-url"]')?.content ||
            localStorage.getItem('API_BASE_URL') ||
            localStorage.getItem('VITE_API_URL');

        if (explicitBaseUrl) {
            console.log(`[Config] Using explicit BASE_URL: ${explicitBaseUrl}`);
            return explicitBaseUrl.replace(/\/+$/, '');
        }

        const port = window.location.port;
        const hostname = window.location.hostname;
        console.log(`[Config] Detect Hostname: '${hostname}', Port: '${port}'`);

        // ── Production: khangjv.id.vn → Render Backend ──
        const renderBackendUrl = 'https://dermatology-diagnosis-model.onrender.com';
        if (hostname === 'khangjv.id.vn' || hostname === 'www.khangjv.id.vn' || hostname.endsWith('.onrender.com')) {
            console.log('[Config] Environment: Production (Render)');
            return renderBackendUrl;
        }

        // ── Local: localhost / 127.0.0.1 → Local Backend (port 8000) ──
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            console.log('[Config] Environment: Local (Direct to 8000)');
            return 'http://localhost:8000';
        }

        // Default: Dùng relative path cho các trường hợp khác (ví dụ: Nginx proxy trên server riêng)
        console.log('[Config] Environment: Default (Relative Path)');
        return '';
    })(),

    // Tiền tố cho API v1 (Phiên bản đầu tiên)
    V1_PREFIX: '/api/v1',

    // Các API Endpoints (đường dẫn xử lý)
    ENDPOINTS: {
        HEALTH: '/health',
        LOGIN: '/api/v1/auth/login',
        REGISTER: '/api/v1/auth/register',
        PREDICT: '/api/v1/predict',
        PREVIEW: '/api/v1/predict/preview',
        GRADCAM: '/api/v1/gradcam',
        FEEDBACK: '/api/v1/feedback',
        HISTORY: '/api/v1/history',
        DIAGNOSIS: (id) => `/api/v1/history/${id}`
    },

    // Cài đặt cho mỗi request (yêu cầu)
    TIMEOUT: 60000, // Thay đổi thành 60 giây (để chờ AI model chạy suy luận)

    // Cài đặt cho việc upload ảnh lên máy chủ
    MAX_FILE_SIZE_MB: 10,
    ALLOWED_EXTENSIONS: ['jpg', 'jpeg', 'png', 'heic']
};

// Xuất ra để sử dụng trong các tệp mã nguồn JS khác
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}
