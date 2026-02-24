/**
 * Cấu hình API
 * Cấu hình tập trung cho các endpoint API
 */

const API_CONFIG = {
    // URL cơ sở cho Backend API
    // - Docker/Nginx (port 80/8080): chuỗi rỗng → nginx sẽ proxy /api/ tới backend
    // - Chạy local (DEV) qua run.py (port 3000): gọi trực tiếp tới localhost:8000
    BASE_URL: (() => {
        const port = window.location.port;
        const hostname = window.location.hostname;
        console.log(`[Config] Detect Port: '${port}', Hostname: '${hostname}'`);

        // Môi trường Local Dev (run.py khởi chạy frontend ở port 3000, 5500, hoặc python -m http.server 8080)
        // Nếu cổng là 8080 mà chạy hostname localhost, có thể là dev server, return localhost:8000
        if (port === '3000' || port === '5500' || port === '8000' || ((port === '8080' || port === '80') && (hostname === 'localhost' || hostname === '127.0.0.1'))) {
            // Trường hợp chạy docker compose, nhưng Nginx có thể đang chặn hoặc lỗi proxy, ta trỏ thẳng
            // Tuy nhiên, đối với docker, tốt nhất là dùng relative path để nginx proxy.
            // Để dung hoà: Nếu người dùng báo lỗi API trên localhost, trả về thẳng localhost:8000
            return 'http://localhost:8000';
        }

        // Môi trường Docker/Production (Dùng domain hoặc IP thật) -> Sử dụng đường dẫn tương đối để nginx proxy
        console.log('[Config] Using relative API path (Docker/Nginx)');
        return '';
    })(),

    // Tiền tố cho API v1 (Phiên bản đầu tiên)
    V1_PREFIX: '/api/v1',

    // Các API Endpoints (đường dẫn xử lý)
    ENDPOINTS: {
        HEALTH: '/health',
        PREDICT: '/api/v1/predict',
        PREVIEW: '/api/v1/predict/preview',
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
