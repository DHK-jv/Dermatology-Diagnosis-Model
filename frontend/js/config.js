/**
 * API Configuration
 * Centralized API endpoint configuration
 */

const API_CONFIG = {
    // Backend API base URL
    // - Docker/Nginx (port 80/8080): empty string → nginx proxies /api/ to backend
    // - Local dev via run.py (port 3000): direct call to localhost:8000
    BASE_URL: (() => {
        const port = window.location.port;
        if (port === '3000' || port === '8000') {
            return 'http://localhost:8000';  // Local dev: gọi thẳng backend
        }
        return '';  // Docker/Nginx: dùng same-origin (nginx proxy /api/)
    })(),

    // API v1 prefix
    V1_PREFIX: '/api/v1',

    // Endpoints
    ENDPOINTS: {
        HEALTH: '/health',
        PREDICT: '/api/v1/predict',
        PREVIEW: '/api/v1/predict/preview',
        GRADCAM: '/api/v1/gradcam',
        HISTORY: '/api/v1/history',
        DIAGNOSIS: (id) => `/api/v1/history/${id}`
    },

    // Request settings
    TIMEOUT: 60000, // 60 seconds for model inference

    // Image upload settings
    MAX_FILE_SIZE_MB: 10,
    ALLOWED_EXTENSIONS: ['jpg', 'jpeg', 'png', 'heic']
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}
