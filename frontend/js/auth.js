/**
 * Module Xác thực
 * Xử lý việc Đăng nhập, Đăng ký và Quản lý Token
 */

class AuthManager {
    constructor() {
        this.tokenKey = 'access_token';
        this.userKey = 'user_info';

        this.init();
    }

    init() {
        // Theo dõi tham số URL để bật popup chuyển hướng tới đăng nhập
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('login') === 'true') {
            // Chờ cho trang (DOM) tải tải xong toàn bộ
            setTimeout(() => this.showAuthModal(), 500);

            // Dọn dẹp gọn lại URL
            urlParams.delete('login');
            const newUrl = window.location.pathname + (urlParams.toString() ? `?${urlParams.toString()}` : '');
            window.history.replaceState({}, document.title, newUrl);
        }

        // Cập nhật Giao diện (UI) dựa trên trạng thái đã đăng nhập hay chưa
        document.addEventListener('DOMContentLoaded', () => {
            this.updateHeaderUI();
            this.injectAuthModal();
        });
    }

    isAuthenticated() {
        return !!localStorage.getItem(this.tokenKey);
    }

    getUser() {
        const user = localStorage.getItem(this.userKey);
        return user ? JSON.parse(user) : null;
    }

    async login(username, password) {
        try {
            showLoader('Đang đăng nhập...');

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const data = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LOGIN}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString()
            });

            localStorage.setItem(this.tokenKey, data.access_token);
            localStorage.setItem(this.userKey, JSON.stringify(data.user));

            this.updateHeaderUI();
            this.hideAuthModal();
            showSuccess(`Xin chào, ${data.user.full_name || data.user.username}!`);

            // Phát đi sự kiện (event) để các module khác nhận diện và xử lý
            window.dispatchEvent(new CustomEvent('auth:login', { detail: data.user }));

            return true;
        } catch (error) {
            showError(error.message);
            return false;
        } finally {
            hideLoader();
        }
    }

    async register(username, password, fullName) {
        try {
            showLoader('Đang tạo tài khoản...');

            const payload = {
                username: username,
                password: password,
                full_name: fullName,
                role: 'user'
            };

            const data = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REGISTER}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            showSuccess('Đăng ký thành công! Đang tự động đăng nhập...');

            // Tự động đăng nhập luôn sau khi đăng ký thành công
            return await this.login(username, password);

        } catch (error) {
            showError(error.message);
            return false;
        } finally {
            hideLoader();
        }
    }

    logout() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        this.updateHeaderUI();

        // Phát đi sự kiện thông báo đăng xuất
        window.dispatchEvent(new Event('auth:logout'));

        showSuccess('Đã đăng xuất');

        // Nếu người dùng đang ở một trang yêu cầu quyền đặc biệt, chuyển hướng đi chỗ khác
        if (window.location.pathname.includes('/history.html')) {
            setTimeout(() => {
                window.location.href = '../index.html';
            }, 1000);
        }
    }

    updateHeaderUI() {
        const user = this.getUser();

        // Chúng ta sẽ tự động tạo hoặc cập nhật menu người dùng trên thanh tiêu đề (header)
        const headerRights = document.querySelectorAll('header .hidden.md\\:flex.items-center.gap-8, header .flex.items-center.gap-8');

        headerRights.forEach(headerRight => {
            // Xóa các thành phần hiển thị xác thực cũ nếu có tồn tại
            const existingAuth = headerRight.querySelector('.auth-container');
            if (existingAuth) existingAuth.remove();

            const authContainer = document.createElement('div');
            authContainer.className = 'auth-container flex items-center gap-4 border-l border-slate-200 dark:border-slate-700 pl-6 ml-2';

            if (user) {
                // Giao diện (UI) chế độ ĐÃ ĐĂNG NHẬP
                authContainer.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                            ${(user.full_name || user.username).charAt(0).toUpperCase()}
                        </div>
                        <div class="flex flex-col">
                            <span class="text-sm font-bold text-slate-800 dark:text-gray-200 leading-none">${user.full_name || user.username}</span>
                            <button id="btn-logout" class="text-xs text-slate-500 hover:text-red-500 text-left mt-1 transition">Đăng xuất</button>
                        </div>
                    </div>
                `;
            } else {
                // Giao diện (UI) chế độ CHƯA ĐĂNG NHẬP
                authContainer.innerHTML = `
                    <button id="btn-show-login" class="text-slate-600 dark:text-slate-300 text-sm font-bold hover:text-primary transition-colors">
                        Đăng nhập
                    </button>
                    <button id="btn-show-register" class="h-9 px-4 rounded-lg border border-primary text-primary text-sm font-bold hover:bg-primary/5 transition-colors">
                        Đăng ký
                    </button>
                `;
            }

            headerRight.appendChild(authContainer);

            // Đính kèm các sự kiện lắng nghe (event listeners)
            if (user) {
                const btnLogout = authContainer.querySelector('#btn-logout');
                if (btnLogout) btnLogout.addEventListener('click', () => this.logout());
            } else {
                const btnLogin = authContainer.querySelector('#btn-show-login');
                const btnRegister = authContainer.querySelector('#btn-show-register');

                if (btnLogin) btnLogin.addEventListener('click', () => this.showAuthModal('login'));
                if (btnRegister) btnRegister.addEventListener('click', () => this.showAuthModal('register'));
            }
        });
    }

    injectAuthModal() {
        // Chỉ chèn cấu trúc html modal popup này một lần duy nhất
        if (document.getElementById('auth-modal')) return;

        const modalHtml = `
            <div id="auth-modal" class="hidden fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm transition-opacity opacity-0">
                <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform scale-95 transition-transform duration-300">
                    <!-- Nút Đóng Popup -->
                    <button id="auth-modal-close" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                    
                    <div class="p-8">
                        <!-- Khung Tiêu Đề -->
                        <div class="text-center mb-8">
                            <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 text-primary mb-4">
                                <span class="material-symbols-outlined text-2xl">dermatology</span>
                            </div>
                            <h2 id="auth-title" class="text-2xl font-bold text-slate-800 dark:text-white">Đăng Nhập</h2>
                            <p id="auth-subtitle" class="text-sm text-slate-500 dark:text-slate-400 mt-2">Chào mừng bạn quay trở lại với MedAI</p>
                        </div>

                        <!-- Các Biểu Mẫu Nhập Liệu -->
                        <div id="login-form-container">
                            <form id="login-form" class="space-y-4" onsubmit="event.preventDefault(); auth.login(this.username.value, this.password.value)">
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tên đăng nhập</label>
                                    <input type="text" name="username" required placeholder="Nhập tên đăng nhập của bạn" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent transition">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Mật khẩu</label>
                                    <input type="password" name="password" required placeholder="Nhập mật khẩu" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent transition">
                                </div>
                                <button type="submit" class="w-full h-11 bg-primary hover:bg-primary-hover text-white font-bold rounded-lg shadow-md transition transform active:scale-[0.98]">
                                    Đăng Nhập
                                </button>
                            </form>
                            <p class="text-center text-sm text-slate-600 dark:text-slate-400 mt-6">
                                Chưa có tài khoản? <a href="#" id="link-to-register" class="text-primary font-semibold hover:underline">Đăng ký ngay</a>
                            </p>
                        </div>

                        <div id="register-form-container" class="hidden">
                            <form id="register-form" class="space-y-4" onsubmit="event.preventDefault(); auth.register(this.username.value, this.password.value, this.fullname.value)">
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Họ và tên</label>
                                    <input type="text" name="fullname" required placeholder="Nhập họ và tên" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent transition">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tên đăng nhập</label>
                                    <input type="text" name="username" required pattern="[a-zA-Z0-9_]{3,20}" title="3-20 ký tự, viết liền không dấu" placeholder="Nhập tên đăng nhập" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent transition">
                                    <p class="text-[11px] text-slate-500 mt-1">3-20 ký tự, viết liền không dấu, có thể dùng số và "_".</p>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Mật khẩu</label>
                                    <input type="password" name="password" required pattern="(?=.*\\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*]).{8,}" title="Ít nhất 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt" placeholder="Nhập mật khẩu" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent transition">
                                    <p class="text-[11px] text-slate-500 mt-1">Tối thiểu 8 ký tự, gồm chữ hoa, chữ thường, chữ số và ký tự đặc biệt (!@#$)</p>
                                </div>
                                <button type="submit" class="w-full h-11 bg-primary hover:bg-primary-hover text-white font-bold rounded-lg shadow-md transition transform active:scale-[0.98]">
                                    Tạo Tài Khoản
                                </button>
                            </form>
                            <p class="text-center text-sm text-slate-600 dark:text-slate-400 mt-6">
                                Đã có tài khoản? <a href="#" id="link-to-login" class="text-primary font-semibold hover:underline">Đăng nhập</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Thiết lập các sự kiện tương tác cho modal popup
        const modal = document.getElementById('auth-modal');
        const modalInner = modal.querySelector('div');
        const closeBtn = document.getElementById('auth-modal-close');
        const linkToReg = document.getElementById('link-to-register');
        const linkToLog = document.getElementById('link-to-login');

        closeBtn.addEventListener('click', () => this.hideAuthModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.hideAuthModal();
        });

        linkToReg.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchModalView('register');
        });

        linkToLog.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchModalView('login');
        });
    }

    showAuthModal(view = 'login') {
        this.injectAuthModal(); // Đảm bảo modal này đã được tạo và tồn tại trên HTML

        const modal = document.getElementById('auth-modal');
        const modalInner = modal.querySelector('div');

        this.switchModalView(view);

        modal.classList.remove('hidden');
        // Kích hoạt vẽ lại (Trigger reflow) bằng mẹo js
        void modal.offsetWidth;

        modal.classList.remove('opacity-0');
        modalInner.classList.remove('scale-95');
        modalInner.classList.add('scale-100');
    }

    hideAuthModal() {
        const modal = document.getElementById('auth-modal');
        if (!modal) return;

        const modalInner = modal.querySelector('div');

        modal.classList.add('opacity-0');
        modalInner.classList.remove('scale-100');
        modalInner.classList.add('scale-95');

        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300); // thời gian chờ đồng bộ hóa với thời lượng hoàn thành hiệu ứng mờ dần trong css
    }

    switchModalView(view) {
        const title = document.getElementById('auth-title');
        const subtitle = document.getElementById('auth-subtitle');
        const loginContainer = document.getElementById('login-form-container');
        const regContainer = document.getElementById('register-form-container');

        if (view === 'register') {
            title.textContent = 'Đăng Ký';
            subtitle.textContent = 'Tạo tài khoản mới để lưu lịch sử chẩn đoán';
            loginContainer.classList.add('hidden');
            regContainer.classList.remove('hidden');
        } else {
            title.textContent = 'Đăng Nhập';
            subtitle.textContent = 'Chào mừng bạn quay trở lại với MedAI';
            regContainer.classList.add('hidden');
            loginContainer.classList.remove('hidden');
        }
    }
}

// Xuất (export) instance mẫu dùng chung (singleton) ra biến toàn cục
const auth = new AuthManager();
window.auth = auth;
