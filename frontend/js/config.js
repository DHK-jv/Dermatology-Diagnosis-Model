/**
 * API Configuration
 * Centralized API endpoint configuration
 */

const API_CONFIG = {
    // Backend API base URL
    BASE_URL: 'http://localhost:8000',

    // API v1 prefix
    V1_PREFIX: '/api/v1',

    // Endpoints
    ENDPOINTS: {
        HEALTH: '/health',
        PREDICT: '/api/v1/predict',
        PREVIEW: '/api/v1/predict/preview',
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
