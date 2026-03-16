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

        // ── Production: khangjv.id.vn → VPS Nginx (Relative Path) ──
        if (hostname === 'khangjv.id.vn' || hostname === 'www.khangjv.id.vn') {
            console.log('[Config] Environment: Production (VPS)');
            return ''; // Nginx handles /api -> backend proxy
        }

        // ── Local: localhost / 127.0.0.1 → Local Backend (port 8000) ──
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            console.log('[Config] Environment: Local (Direct to 8000)');
            return 'http://localhost:8000';
        }

        // Default: Dùng relative path cho các trường hợp khác
        console.log('[Config] Environment: Default (Relative Path)');
        return '';
    })(),

    // Tiền tố cho API (VPS dùng /api)
    V1_PREFIX: '/api',

    // Các API Endpoints
    ENDPOINTS: {
        HEALTH: '/health',
        LOGIN: '/api/auth/login',
        REGISTER: '/api/auth/register',
        PREDICT: '/api/predict',
        PREVIEW: '/api/predict/preview',
        GRADCAM: '/api/gradcam',
        FEEDBACK: '/api/feedback',
        HISTORY: '/api/history',
        DIAGNOSIS: (id) => `/api/history/${id}`
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
