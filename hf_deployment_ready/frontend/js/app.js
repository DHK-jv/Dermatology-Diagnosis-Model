/**
 * Logic Cốt Lõi Của App
 * Điều hướng, chuyển giao diện, và các chức năng dùng chung
 */

// Khởi tạo app khi trang HTML (DOM) đã được tải xong
document.addEventListener('DOMContentLoaded', function () {
    console.log('MedAI Frontend initialized');

    // Thiết lập điều hướng
    setupNavigation();

    // Thiết lập nút chuyển giao diện (nếu có)
    setupThemeToggle();

    // Kiểm tra kết nối tới backend
    checkBackendHealth();
});

/**
 * Cài đặt các trình xử lý điều hướng
 */
function setupNavigation() {
    // Lấy tất cả các thẻ liên kết điều hướng
    const navLinks = document.querySelectorAll('a[href]');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        // Cập nhật các liên kết tương đối để hoạt động khớp với cấu trúc thư mục của dự án
        if (href && !href.startsWith('http') && !href.startsWith('#')) {
            // Đảm bảo các liên kết hoạt động tốt từ các cấp độ thư mục khác nhau
            if (href.startsWith('pages/')) {
                // Đã chính xác nếu dùng từ file index.html
            } else if (href === 'index.html' || href === '/') {
                // Quay trở lại trang chủ index từ thư mục con (pages)
                const currentPath = window.location.pathname;
                if (currentPath.includes('/pages/')) {
                    link.setAttribute('href', '../index.html');
                }
            }
        }
    });
}

/**
 * Thiết lập tính năng chuyển đổi giao diện sáng/tối
 */
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');

    if (!themeToggle) return;

    // Kiểm tra cấu hình giao diện đã được lưu vào máy
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.classList.toggle('dark', currentTheme === 'dark');

    // Chuyển đổi giao diện khi nhấn chuột vào nút
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

/**
 * Kiểm tra sức khỏe của API Backend
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✓ Backend API is healthy:', data);

            if (!data.model_loaded) {
                console.warn('⚠ AI Model not loaded on backend');
            }
        } else {
            console.warn('⚠ Backend API health check failed');
        }
    } catch (error) {
        console.error('✗ Cannot connect to backend API:', error.message);
        console.error('Make sure backend is running at:', API_CONFIG.BASE_URL);
    }
}

/**
 * Điều hướng tới một trang mới cùng với trạng thái (state) truyền kèm theo
 * @param {string} url - Đường dẫn URL của trang web
 * @param {object} state - Biến trạng thái để truyền sang trang kia
 */
function navigateTo(url, state = {}) {
    if (Object.keys(state).length > 0) {
        // Lưu trữ lại biến trạng thái cho trang tiếp theo sử dụng
        sessionStorage.setItem('navigationState', JSON.stringify(state));
    }
    window.location.href = url;
}

/**
 * Đọc thuộc tính trạng thái (state) được đẩy từ trang trước sang
 * @returns {object} Trả về đối tượng trạng thái hoặc Null
 */
function getNavigationState() {
    try {
        const state = sessionStorage.getItem('navigationState');
        if (state) {
            sessionStorage.removeItem('navigationState');
            return JSON.parse(state);
        }
    } catch (e) {
        console.error('Failed to get navigation state:', e);
    }
    return null;
}
