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
    const { hostname, port, protocol } = window.location;
    console.log(`[Config] Detect → hostname='${hostname}' port='${port}' protocol='${protocol}'`);

    // ── Ưu tiên 1: Local development (Luôn trỏ về 8000 nếu là localhost) ──
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        const effectivePort = port || (protocol === 'https:' ? '443' : '80');
        const proxyPorts = new Set(['80', '8080', '7860']);

        if (proxyPorts.has(effectivePort)) {
            console.log('[Config] Environment: Unified/Proxy → relative path');
            return '';
        }

        console.log('[Config] Environment: Local dev server → http://localhost:8000');
        return 'http://localhost:8000';
    }

    // ── Ưu tiên 2-4: Giá trị tường minh (Chỉ áp dụng khi không phải local) ──
    const explicit =
        (typeof window !== 'undefined' && window.__API_BASE_URL__) ||
        document.querySelector('meta[name="api-base-url"]')?.content ||
        _safeLocalStorageGet('API_BASE_URL') ||
        _safeLocalStorageGet('VITE_API_URL');

    if (explicit) {
        console.log(`[Config] Using explicit BASE_URL: ${explicit}`);
        return explicit.replace(/\/+$/, '');
    }

    // 4b. Custom domain (khangjv.id.vn)
    if (hostname === 'khangjv.id.vn' || hostname === 'www.khangjv.id.vn') {
        if (protocol === 'https:') {
            const hfBackend = 'https://hoangkhang2-medai-dermatology.hf.space';
            console.log(`[Config] Environment: Production (HF Spaces backend) → ${hfBackend}`);
            return hfBackend;
        }
        // HTTP = đang test qua Nginx local → relative path
        console.log('[Config] Environment: Local Nginx proxy → relative path');
        return '';
    }

    // 4c. Hugging Face Spaces
    if (hostname.endsWith('.hf.space')) {
        console.log('[Config] Environment: Hugging Face Spaces → relative path');
        return '';
    }

    // Mặc định: relative path cho mọi môi trường còn lại
    console.log('[Config] Environment: Default → relative path');
    return '';
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
