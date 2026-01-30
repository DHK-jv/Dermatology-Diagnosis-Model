/**
 * Utility Functions
 * Helper functions for API calls, validation, formatting, etc.
 */

/**
 * Make an API call with error handling
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Response data
 */
async function apiCall(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
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
 * Validate image file
 * @param {File} file - Image file to validate
 * @returns {object} {valid: boolean, error: string}
 */
function validateImage(file) {
    // Check if file exists
    if (!file) {
        return { valid: false, error: 'Vui lòng chọn file ảnh' };
    }

    // Check file extension
    const extension = file.name.split('.').pop().toLowerCase();
    if (!API_CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            error: `Định dạng file không hợp lệ. Chỉ chấp nhận: ${API_CONFIG.ALLOWED_EXTENSIONS.join(', ')}`
        };
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > API_CONFIG.MAX_FILE_SIZE_MB) {
        return {
            valid: false,
            error: `File quá lớn (${fileSizeMB.toFixed(1)}MB). Kích thước tối đa: ${API_CONFIG.MAX_FILE_SIZE_MB}MB`
        };
    }

    // Check MIME type
    if (!file.type.startsWith('image/')) {
        return { valid: false, error: 'File không phải là ảnh hợp lệ' };
    }

    return { valid: true, error: '' };
}

/**
 * Format date to Vietnamese readable format
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
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
 * Format date to short format
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDateShort(date) {
    const d = typeof date === 'string' ? new Date(date) : date;

    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    return `${day}/${month}/${year}`;
}

/**
 * Show loading indicator
 * @param {string} message - Loading message
 */
function showLoader(message = 'Đang xử lý...') {
    // Create loader overlay if doesn't exist
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

    // Update message
    const messageEl = document.getElementById('loader-message');
    if (messageEl) {
        messageEl.textContent = message;
    }

    loader.classList.remove('hidden');
}

/**
 * Hide loading indicator
 */
function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

/**
 * Show error toast notification
 * @param {string} message - Error message
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * Show success toast notification
 * @param {string} message - Success message
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show toast notification
 * @param {string} message - Notification message
 * @param {string} type - Type: 'success', 'error', 'info'
 */
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existing = document.querySelectorAll('.toast-notification');
    existing.forEach(t => t.remove());

    // Create toast
    const toast = document.createElement('div');
    toast.className = 'toast-notification fixed top-4 right-4 z-50 max-w-md bg-white dark:bg-slate-800 rounded-lg shadow-xl border-l-4 p-4 animate-slide-in';

    // Set border color based on type
    const colors = {
        success: 'border-green-500',
        error: 'border-red-500',
        info: 'border-blue-500'
    };
    toast.classList.add(colors[type] || colors.info);

    // Icon
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

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Get risk level badge HTML
 * @param {string} riskLevel - Risk level: 'low', 'medium', 'high', 'very_high'
 * @param {string} riskLevelVi - Vietnamese risk level text
 * @returns {string} HTML string for badge
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
 * Store data in localStorage
 * @param {string} key - Storage key
 * @param {any} value - Value to store
 */
function store(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Failed to store data:', e);
    }
}

/**
 * Retrieve data from localStorage
 * @param {string} key - Storage key
 * @returns {any} Stored value or null
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
 * Navigate to a page with optional query params
 * @param {string} path - Target page path
 * @param {object} params - Query parameters
 */
function navigateTo(path, params = {}) {
    const url = new URL(path, window.location.origin);

    // Add query params
    Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
            url.searchParams.set(key, params[key]);
        }
    });

    window.location.href = url.toString();
}

/**
 * Get URL parameter by name
 * @param {string} name - Parameter name
 * @returns {string|null} Parameter value
 */
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Add animation styles
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
