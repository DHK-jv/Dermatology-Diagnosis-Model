/**
 * Các Hàm Tiện Ích (Utility Functions)
 * Các hàm hỗ trợ cho việc gọi API, xác thực, định dạng hóa, v.v
 */

/**
 * Thực thi việc gọi API kết hợp với cơ chế bắt lỗi và đính kèm Xác Thực (Authentication)
 * @param {string} url - Đường dẫn đích của API
 * @param {object} options - Cấu hình truy vấn
 * @returns {Promise<object>} Dữ liệu JSON phản hồi
 */
async function apiCall(url, options = {}) {
    console.log(`[API] Call: ${options.method || 'GET'} ${url}`);
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

    try {
        // Chuẩn bị header và nhét token xác thực vào nếu có tồn tại
        const headers = { ...options.headers };
        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Ngăn chặn việc vô ý ghi đè các cấu hình config cũ
        const fetchOptions = {
            ...options,
            headers,
            signal: controller.signal
        };

        const response = await fetch(url, fetchOptions);

        clearTimeout(timeout);

        if (!response.ok) {
            if (response.status === 401) {
                // Token đã quá hạn hoặc không còn nguyên vẹn
                handleUnauthorized();
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();

    } catch (error) {
        clearTimeout(timeout);

        if (error.name === 'AbortError') {
            throw new Error('Yêu cầu timeout. Vui lòng thử lại.');
        }

        throw error;
    }
}

/**
 * Thực hiện xử lý các phản hồi trả về mã lỗi 401 Unauthorized từ chối Quyền của API
 */
function handleUnauthorized() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');

    // Chỉ chuyển hướng nếu người dùng không thuộc trang chủ nền (nơi bộ đăng nhập có thể đã được tự động xử lý rồi)
    if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
        showError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
        setTimeout(() => {
            window.location.href = '/index.html?login=true';
        }, 1500);
    }
}

/**
 * Xác thực (Validate) tính đúng đắn của tập tin hình ảnh tải lên
 * @param {File} file - Tệp file hình được trỏ
 * @returns {object} {valid: boolean, error: string} Trạng thái hợp lệ kèm báo cáo văn bản
 */
function validateImage(file) {
    // Xác minh file có tồn tại không
    if (!file) {
        return { valid: false, error: 'Vui lòng chọn file ảnh' };
    }

    // Kiểm tra đuôi file mở rộng (extension)
    const extension = file.name.split('.').pop().toLowerCase();
    if (!API_CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            error: `Định dạng file không hợp lệ. Chỉ chấp nhận: ${API_CONFIG.ALLOWED_EXTENSIONS.join(', ')}`
        };
    }

    // Kiểm tra dung lượng file tải lên
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > API_CONFIG.MAX_FILE_SIZE_MB) {
        return {
            valid: false,
            error: `File quá lớn (${fileSizeMB.toFixed(1)}MB). Kích thước tối đa: ${API_CONFIG.MAX_FILE_SIZE_MB}MB`
        };
    }

    // Kiểm tra kiểu MIME tiêu chuẩn nội dung file
    if (!file.type.startsWith('image/')) {
        return { valid: false, error: 'File không phải là ảnh hợp lệ' };
    }

    return { valid: true, error: '' };
}

/**
 * Định dạng format lại ngày giờ cho chuẩn cấu trúc đọc hiểu của người Việt Nam
 * @param {string|Date} date - Đối tượng Dữ liệu ngày cần format
 * @returns {string} Trả về chuỗi ngày tháng sau khi đã format
 */
function formatDate(date) {
    const d = typeof date === 'string' ? new Date(date) : date;

    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };

    return d.toLocaleDateString('vi-VN', options);
}

/**
 * Format định nghĩa cấu trúc ngày tháng kiểu thu gọn (short format)
 * @param {string|Date} date - Object ngày tháng
 * @returns {string} Text Chuỗi ngày rút gọn
 */
function formatDateShort(date) {
    const d = typeof date === 'string' ? new Date(date) : date;

    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    return `${day}/${month}/${year}`;
}

/**
 * Hiển thị lên màn hình trạng thái báo đang chờ xử lý (Loading indicator)
 * @param {string} message - Thông báo mô tả tiến trình đang load gì
 */
function showLoader(message = 'Đang xử lý...') {
    // Tạo thêm lớp nền phủ loading trong trường hợp nó được gỡ xóa trên trình duyệt
    let loader = document.getElementById('global-loader');

    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center';
        loader.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4 max-w-sm">
                <div class="animate-spin rounded-full h-16 w-16 border-4 border-primary border-t-transparent"></div>
                <p id="loader-message" class="text-slate-700 dark:text-slate-200 font-medium text-center"></p>
            </div>
        `;
        document.body.appendChild(loader);
    }

    // Cập nhật thẻ text thông điệp
    const messageEl = document.getElementById('loader-message');
    if (messageEl) {
        messageEl.textContent = message;
    }

    loader.classList.remove('hidden');
}

/**
 * Ẩn và che đi màn hình thông báo tải giao diện Loader
 */
function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

/**
 * Hiển thị khối hộp Pop Toast thông báo xảy ra lỗi (Error)
 * @param {string} message - Nội dung báo lỗi mô tả
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * Hiển thị hộp loại Toast thông báo trạng thái thao tác thành công (Success)
 * @param {string} message - Thông điệp vinh quang
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Hiển thị khối hộp Toast thông báo nhanh bao quát cho UI ứng dụng
 * @param {string} message - Dòng Lời thông báo nội dung
 * @param {string} type - Chuẩn báo hiệu cờ Type flag trạng thái: 'success', 'error', 'info'
 */
function showToast(message, type = 'info') {
    // Xóa đi các dòng thông báo toast cũ hiện tại
    const existing = document.querySelectorAll('.toast-notification');
    existing.forEach(t => t.remove());

    // Tạo thiết lập khối cấu trúc hộp thoại thẻ html pop toast
    const toast = document.createElement('div');
    toast.className = 'toast-notification fixed top-4 right-4 z-50 max-w-md bg-white dark:bg-slate-800 rounded-lg shadow-xl border-l-4 p-4 animate-slide-in';

    // Thiết lập chọn loại màu Border viền theo trạng thái báo (type)
    const colors = {
        success: 'border-green-500',
        error: 'border-red-500',
        info: 'border-blue-500'
    };
    toast.classList.add(colors[type] || colors.info);

    // Biểu tượng Icon trang trí
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <div class="flex items-start gap-3">
            <div class="flex-shrink-0 w-6 h-6 rounded-full bg-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'}-100 flex items-center justify-center text-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'}-600 font-bold">
                ${icons[type] || icons.info}
            </div>
            <p class="flex-1 text-sm text-slate-700 dark:text-slate-200">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="text-slate-400 hover:text-slate-600">
                ✕
            </button>
        </div>
    `;

    document.body.appendChild(toast);

    // Cài đặt hẹn giờ Tự động tắt thu hồi toast HTML sau khi tròn 5 giây hiển thị
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Sinh ra thẻ nhãn HTML phân cấp độ Nguy rủi ro do nhãn dán (Risk badge HTML)
 * @param {string} riskLevel - Loại cảnh báo dán nhãn: 'low', 'medium', 'high', 'very_high'
 * @param {string} riskLevelVi - Tiếng việt mô tả cho nhãn rủi ro đó
 * @returns {string} Trả về cấu trúc chuỗi HTML trần cho huy hiệu badge
 */
function getRiskBadge(riskLevel, riskLevelVi) {
    const badges = {
        low: `<span class="px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 text-xs font-bold border border-green-200 dark:border-green-900/50">
            ${riskLevelVi}
        </span>`,
        medium: `<span class="px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 text-xs font-bold border border-yellow-200 dark:border-yellow-900/50">
            ${riskLevelVi}
        </span>`,
        high: `<span class="px-3 py-1 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 text-xs font-bold border border-red-200 dark:border-red-900/50">
            ${riskLevelVi}
        </span>`,
        very_high: `<span class="px-3 py-1 rounded-full bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-200 text-xs font-bold border border-red-300 dark:border-red-900/50">
            ⚠️ ${riskLevelVi}
        </span>`
    };

    return badges[riskLevel] || badges.medium;
}

/**
 * Nạp khóa dữ liệu vô kho lưu trữ LocalStorage nội bộ trình duyệt user browser
 * @param {string} key - Tên chìa khóa (Key)
 * @param {any} value - Nội dung Giá trị quy định cho ghi lại
 */
function store(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Failed to store data:', e);
    }
}

/**
 * Truy xuất lấy ra khối dữ liệu đang nắm tại bộ lưu trữ localStorage trình duyệt ra sử dụng
 * @param {string} key - Tên chìa khóa truy vấn truy cập vào Storage
 * @returns {any} Giá trị của JSON kho đó hoặc lấy rác rỗng Null
 */
function retrieve(key) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    } catch (e) {
        console.error('Failed to retrieve data:', e);
        return null;
    }
}

/**
 * Di chuyển điều hướng sang trang URL HTML khác được phép đưa kèm theo tham số thông điệp truy vấn Query (URL Params) qua trang mới
 * @param {string} path - URL đường dẫn của file thẻ HTML đích điểm nhắm tới
 * @param {object} params - Object Dictionary bao các giá trị tham số cấp kèm theo
 */
function navigateTo(path, params = {}) {
    const url = new URL(path, window.location.origin);

    // Móc gắn các thông tin biến dữ liệu Params vào sau đường dẫn truyền lệnh URL Query
    // Xây query params
    Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
            url.searchParams.set(key, params[key]);
        }
    });

    window.location.href = url.toString();
}

/**
 * Đọc tham khảo rút trích xuất Query param biến số theo tên quy ước chỉ định trên URL parameters
 * @param {string} name - Tên đối số (query param)
 * @returns {string|null} Trả về mảng text thông tin của cấu hình URL get var
 */
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Thêm nhúng các cụm chỉ định định dạng chuyển cảnh Animation bổ trợ cho ứng dụng bằng CSS inline
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
