/**
 * Cấu hình API
 * Cấu hình tập trung cho các endpoint API
 */

/**
 * Đọc giá trị từ localStorage một cách an toàn.
 * Một số trình duyệt (Safari ITP, iframe sandboxed) ném SecurityError khi truy cập storage.
 * @param {string} key
 * @returns {string|null}
 */
function _safeLocalStorageGet(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

/**
 * Phát hiện BASE_URL phù hợp với môi trường hiện tại.
 * Thứ tự ưu tiên:
 *   1. window.__API_BASE_URL__   (inject lúc server-side render)
 *   2. <meta name="api-base-url"> (inject qua HTML template)
 *   3. localStorage['API_BASE_URL'] hoặc localStorage['VITE_API_URL']  (override thủ công)
 *   4. Tự phát hiện theo hostname / port
 * @returns {string}
 */
function _resolveBaseUrl() {
    // ── Cấu hình cố định cho môi trường PRODUCTION (khangjv.id.vn) ──
    const PROD_BACKEND = 'https://hoangkhang2-medai-dermatology.hf.space';
    
    // Nếu chạy trực tiếp trên HF Space thì dùng path tương đối
    if (window.location.hostname.endsWith('.hf.space')) {
        console.log('[Config] Environment: Hugging Face Native → relative path');
        return '';
    }

    // Mọi trường hợp khác (khangjv.id.vn) đều gọi về HF Backend
    console.log(`[Config] Environment: Production (External) → ${PROD_BACKEND}`);
    return PROD_BACKEND;
}

const API_CONFIG = {
    BASE_URL: _resolveBaseUrl(),

    /** Tiền tố API v1 */
    V1_PREFIX: '/api/v1',

    /** Các endpoint */
    ENDPOINTS: {
        HEALTH:    '/health',
        LOGIN:     '/api/v1/auth/login',
        REGISTER:  '/api/v1/auth/register',
        PREDICT:   '/api/v1/predict',
        PREVIEW:   '/api/v1/predict/preview',
        GRADCAM:   '/api/v1/gradcam',
        FEEDBACK:  '/api/v1/feedback',
        HISTORY:   '/api/v1/history',
        DIAGNOSIS: (id) => `/api/v1/history/${id}`,
    },

    /** Timeout mỗi request (ms) — đủ dài cho AI inference */
    TIMEOUT: 60_000,

    /** Giới hạn upload ảnh */
    MAX_FILE_SIZE_MB: 10,
    ALLOWED_EXTENSIONS: ['jpg', 'jpeg', 'png', 'heic'],
};

// Xuất (export) ra biến toàn cục để các file khác (utils.js, auth.js...) có thể dùng
window.API_CONFIG = API_CONFIG;

// CommonJS export (Node / bundler cũ)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}
