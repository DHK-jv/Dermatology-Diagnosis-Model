/**
 * Hệ Thống Bảng Quản Trị (Admin Dashboard)
 * Lấy các thống kê biểu đồ con số, danh sách người dùng, và quản lý các quyền truy cập
 */

let allUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Kiểm tra lại Xác thực (Auth) & Quyền/Vai trò (Role)
    const user = auth.getUser();
    if (!user) {
        window.location.href = 'index.html?login=true';
        return;
    }
    if (user.role !== 'admin') {
        alert('Bạn không có quyền truy cập trang này. Vui lòng đăng nhập bằng tài khoản Admin.');
        window.location.href = 'index.html';
        return;
    }

    // Cập nhật biểu tượng Ảnh đại diện (Avatar)
    const avatar = document.getElementById('admin-avatar');
    if (avatar) {
        avatar.textContent = (user.full_name || user.username).charAt(0).toUpperCase();
    }

    // 2. Chờ Load Tải Dữ Liệu Khởi Tạo
    await Promise.all([
        loadStats(),
        loadUsers()
    ]);

    // 3. Khởi dựng chức năng ô thanh Tìm Kiếm (Search)
    setupUserSearch();
});

/**
 * Truy xuất Fetch để nạp và render Dữ liệu Thống Kê Dashboard
 */
async function loadStats() {
    try {
        const stats = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.V1_PREFIX}/admin/stats`);

        const container = document.getElementById('stats-container');

        container.innerHTML = `
            <!-- Tổng Số Người Dùng Trỏ Tới -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between group hover:shadow-md transition">
                <div>
                    <p class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Tổng Người Dùng</p>
                    <h3 class="text-3xl font-bold text-slate-800 dark:text-white">${stats.total_users}</h3>
                </div>
                <div class="h-14 w-14 rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition">
                    <span class="material-symbols-outlined">group</span>
                </div>
            </div>

            <!-- Tổng Số Chẩn Đoán Lịch Sử -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between group hover:shadow-md transition">
                <div>
                    <p class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Tổng SL Chẩn Đoán</p>
                    <h3 class="text-3xl font-bold text-slate-800 dark:text-white">${stats.total_diagnoses}</h3>
                </div>
                <div class="h-14 w-14 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 flex items-center justify-center text-2xl group-hover:scale-110 transition">
                    <span class="material-symbols-outlined">analytics</span>
                </div>
            </div>

            <!-- Số Ca Phân Tích Hôm Nay -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between group hover:shadow-md transition">
                <div>
                    <p class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Chẩn Đoán Hôm Nay</p>
                    <h3 class="text-3xl font-bold text-slate-800 dark:text-white">${stats.today_diagnoses}</h3>
                </div>
                <div class="h-14 w-14 rounded-full bg-green-50 dark:bg-green-900/20 text-green-600 flex items-center justify-center text-2xl group-hover:scale-110 transition">
                    <span class="material-symbols-outlined">today</span>
                </div>
            </div>

            <!-- Số Ca Nhận Diện Có Trường Hợp Rủi Ro Cao Nhất -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between group hover:shadow-md transition">
                <div>
                    <p class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Ca Nguy Hiểm Cao</p>
                    <h3 class="text-3xl font-bold text-red-600 dark:text-red-400">${stats.high_risk_cases}</h3>
                </div>
                <div class="h-14 w-14 rounded-full bg-red-50 dark:bg-red-900/20 text-red-600 flex items-center justify-center text-2xl group-hover:scale-110 transition">
                    <span class="material-symbols-outlined">warning</span>
                </div>
            </div>
        `;
    } catch (error) {
        console.error("Failed to load stats", error);
        document.getElementById('stats-container').innerHTML = `<p class="text-red-500 kol-span-4 p-4">Lỗi tải dữ liệu thống kê: ${error.message}</p>`;
    }
}

/**
 * Tải danh sách các users sử dụng và tiến hành kết xuất Table
 */
async function loadUsers() {
    try {
        allUsers = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.V1_PREFIX}/admin/users`);
        renderUsersTable(allUsers);
    } catch (error) {
        console.error("Failed to load users", error);
        document.getElementById('user-table-body').innerHTML = `
            <tr><td colspan="5" class="px-6 py-6 text-center text-red-500">Lỗi tải người dùng: ${error.message}</td></tr>
        `;
    }
}

/**
 * Quét dữ liệu sinh cấu trúc bảng Table HTML
 */
function renderUsersTable(users) {
    const tbody = document.getElementById('user-table-body');
    const currentUser = auth.getUser()?.username;

    if (!users || users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-12 text-center text-gray-500">Không tìm thấy người dùng</td></tr>`;
        return;
    }

    tbody.innerHTML = users.map(user => {
        const isAdmin = user.role === 'admin';
        const roleBadge = isAdmin
            ? `<span class="px-2.5 py-1 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 text-[11px] font-bold border border-purple-200 dark:border-purple-800">ADMIN</span>`
            : `<span class="px-2.5 py-1 rounded bg-slate-100 text-slate-600 dark:bg-slate-700/50 dark:text-slate-300 text-[11px] font-bold border border-slate-200 dark:border-slate-600">USER</span>`;

        const isMe = user.username === currentUser;

        return `
            <tr class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition border-b border-gray-100 dark:border-gray-800 last:border-0">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs uppercase">
                            ${(user.username || '?').charAt(0)}
                        </div>
                        <div>
                            <p class="font-bold text-slate-800 dark:text-white">
                                ${user.username}
                                ${isMe ? `<span class="ml-2 text-[10px] text-gray-400 font-normal">(Bạn)</span>` : ''}
                            </p>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300 font-medium">
                    ${user.full_name || '-'}
                </td>
                <td class="px-6 py-4">
                    ${roleBadge}
                </td>
                <td class="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                    ${user.created_at ? formatDateShort(user.created_at) : '-'}
                </td>
                <td class="px-6 py-4 text-right">
                    ${!isMe ? `
                        <button onclick="toggleRole('${user.username}', '${isAdmin ? 'user' : 'admin'}')" 
                            class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${isAdmin
                    ? 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 dark:bg-red-900/20 dark:border-red-800 dark:hover:bg-red-900/40'
                    : 'bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20'
                }">
                            ${isAdmin ? 'Hạ Quyền' : 'Cấp Admin'}
                        </button>
                    ` : `<span class="text-xs text-gray-400 italic">Không thể tự sửa</span>`}
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Cập Nhật Trao Quyền Role thông báo cho API
 */
window.toggleRole = async function (username, newRole) {
    const actionName = newRole === 'admin' ? 'Cấp quyền Admin' : 'Hạ quyền xuống User';

    if (!confirm(`Xác nhận: ${actionName} cho người dùng [${username}]?`)) return;

    try {
        showLoader(`Đang ${actionName.toLowerCase()}...`);
        await apiCall(
            `${API_CONFIG.BASE_URL}${API_CONFIG.V1_PREFIX}/admin/users/${username}/role?role=${newRole}`,
            { method: 'PUT' }
        );
        showSuccess('Cập nhật quyền thành công!');

        // Làm mới (Reload) cho nạp danh sách lại bảng tải về user table
        await loadUsers();
    } catch (error) {
        showError(`Lỗi: ${error.message}`);
    } finally {
        hideLoader();
    }
}

/**
 * Xử lý nhập liệu văn bản gõ vào khung hộp Tìm Kiếm Search Input
 */
function setupUserSearch() {
    const searchInput = document.getElementById('user-search');
    let timeout = null;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const query = e.target.value.toLowerCase().trim();
            if (!query) {
                renderUsersTable(allUsers);
                return;
            }

            const filtered = allUsers.filter(u =>
                u.username.toLowerCase().includes(query) ||
                (u.full_name && u.full_name.toLowerCase().includes(query))
            );

            renderUsersTable(filtered);
        }, 300);
    });
}
