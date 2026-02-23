/**
 * Logic Của Trang Lịch Sử
 * Lấy về và hiển thị lịch sử chẩn đoán từ API
 */

let historyData = [];
let filteredData = [];
let currentFilter = 'all';

// Khởi tạo quy trình khi trang DOM đã được tải thành công
document.addEventListener('DOMContentLoaded', async function () {
    console.log('History page initialized');

    await loadHistory();
    setupFilters();
    setupSearch();
});

/**
 * Tải danh sách lịch sử truy xuất từ API
 */
async function loadHistory() {
    try {
        // --- 1. CÀI ĐẶT TRẠNG THÁI HIỂN THỊ ĐANG TẢI (LOADING) ---
        const loadingState = document.getElementById('loading-state');
        const historyTable = document.getElementById('history-table');
        const emptyState = document.getElementById('empty-state');
        const tableBody = document.getElementById('history-records');

        // Hiện vòng lặp xoay tròn chờ duyệt tải, ẩn các màn khác
        if (loadingState) loadingState.classList.remove('hidden');
        if (historyTable) historyTable.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');

        // Đồng thời hiển thị thông báo màn hình global_loading chờ dữ liệu về
        showLoader('Đang tải lịch sử...');

        // --- 2. GIAO TIẾP TẢI VỀ DỮ LIỆU ---
        const response = await apiCall(
            API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.HISTORY + '?limit=100'
        );

        // --- 3. XỬ LÝ DỮ LIỆU PHẢN HỒI ---
        if (response && response.records) {
            historyData = response.records;
            filteredData = [...historyData];

            if (response.records.length > 0) {
                // NẾU CÓ DỮ LIỆU: Hiện bảng thống kê
                if (historyTable) historyTable.classList.remove('hidden');
                displayHistory(filteredData);
            } else {
                // NẾU KHÔNG CÓ DỮ LIỆU: Hiện màn hình hộp báo trống
                if (emptyState) emptyState.classList.remove('hidden');
            }

            updateStats(response.records);
        } else {
            showError('Không có dữ liệu lịch sử');
            if (emptyState) emptyState.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Error loading history:', error);
        showError('Lỗi khi tải lịch sử: ' + error.message);
        // Nếu vào ngoại lệ xảy ra Lỗi, hiển thị trạng thái màn rỗng hoặc duy trì thuật toán bắt lỗi cũ
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.classList.remove('hidden');

    } finally {
        // --- 4. DỌN DẸP SẠCH GIAO DIỆN (LUÔN CHẠY DÙ LỖI HAY KHÔNG) ---
        // Luôn luôn thiết lập tắt hiệu ứng loading/spinner
        const loadingState = document.getElementById('loading-state');
        if (loadingState) loadingState.classList.add('hidden');
        hideLoader(); // Ẩn màn hình tải dữ liệu lơ lửng
    }
}

/**
 * Đổ dữ liệu chẩn đoán vào cấu trúc khung HTML của thẻ Table
 * @param {Array} records - Tập hợp các Hồ sơ khám bệnh được trả về
 */
function displayHistory(records) {
    const tableBody = document.getElementById('history-records');

    if (!tableBody) {
        console.error('History table container not found');
        return;
    }

    // Xóa sạch các thẻ dòng cũ đã nhúng trước đó
    const rows = tableBody.querySelectorAll('.bg-white, .bg-gray-900');
    rows.forEach(row => row.remove());

    if (records.length === 0) {
        // Giao diện không có lịch sử sẽ trả hiển thị rỗng
        tableBody.innerHTML += `
            <div class="col-span-12 text-center py-12">
                <span class="material-symbols-outlined text-6xl text-gray-300 dark:text-gray-600">folder_open</span>
                <p class="text-gray-500 dark:text-gray-400 mt-4">Không có dữ liệu</p>
            </div>
        `;
        return;
    }

    // Sản sinh các thành phần phân mảnh HTML cho dòng dữ liệu mới
    records.forEach(record => {
        const row = createHistoryRow(record);
        tableBody.appendChild(row);
    });

    // Cập nhật lượt xem số lượng cho header bảng
    updateRecordCount(records.length, historyData.length);
}

/**
 * Cấu trúc mã code dựng thẻ dòng dữ liệu HTML hiển thị lịch sử
 * @param {object} record - Hồ sơ khám chi tiết của 1 chẩn đoán
 * @returns {HTMLElement} Phần tử html cho Thẻ Dòng (Row)
 */
function createHistoryRow(record) {
    const row = document.createElement('div');
    row.className = 'bg-white dark:bg-gray-900 px-6 py-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow grid grid-cols-12 gap-4 items-center cursor-pointer';

    // Sự kiện được Click vào dòng để xem chi tiết kết quả chẩn đoán này
    row.addEventListener('click', () => {
        viewDiagnosisDetail(record.diagnosis_id);
    });

    // Ta tiến hành làm một phép cắt tách chữ cái làm chữ viết tắt để gán cho hình đại diện (avatar)
    const parts = record.diagnosis_id.split('-');
    const initials = parts.length > 2 ? parts[2].substring(0, 2).toUpperCase() : 'DG';

    // Phân loại cấp độ Màu Cảnh Báo Rủi ro
    const riskColors = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'red',
        'very_high': 'red'
    };
    const riskColor = riskColors[record.risk_level] || 'yellow';

    row.innerHTML = `
        <!-- Thông Tin ID & Bệnh Nhân -->
        <div class="col-span-4 flex items-center gap-3">
            <div class="h-10 w-10 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-primary font-bold">
                ${initials}
            </div>
            <div class="flex flex-col">
                <span class="font-bold text-[#111817] dark:text-white flex items-center gap-2">
                    ${record.diagnosis_id}
                    ${record.user_id ? `<span class="px-2 py-0.5 rounded text-[10px] bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 font-medium">@${record.user_id}</span>` : ''}
                </span>
                <span class="text-xs text-gray-500">${formatDateShort(record.timestamp)}</span>
            </div>
        </div>
        
        <!-- Xem Trước Hình Tổn Thương -->
        <div class="col-span-2 flex justify-center">
            <div class="h-12 w-16 bg-gray-200 dark:bg-gray-700 rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden flex items-center justify-center relative group">
                ${record.image_filename
            ? `<img src="${API_CONFIG.BASE_URL}/uploads/${record.image_filename}" 
                        alt="Diagnosis" 
                        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                        onerror="this.onerror=null; this.parentElement.innerHTML='<span class=\'material-symbols-outlined text-gray-400\'>broken_image</span>'">`
            : '<span class="material-symbols-outlined text-gray-400">image</span>'
        }
            </div>
        </div>
        
        <!-- Chẩn Đoán Xác Định -->
        <div class="col-span-2">
            <span class="px-2.5 py-1 rounded bg-${riskColor}-100 dark:bg-${riskColor}-900/30 text-${riskColor}-600 dark:text-${riskColor}-400 text-xs font-bold">
                ${record.disease_name_vi}
            </span>
        </div>
        
        <!-- Mức Độ Tin Cậy % -->
        <div class="col-span-2">
            <div class="flex items-center gap-2">
                <div class="w-full bg-gray-100 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-${riskColor}-500 h-full rounded-full" style="width: ${(record.confidence * 100).toFixed(0)}%"></div>
                </div>
                <span class="text-xs font-bold text-gray-700 dark:text-gray-300">${(record.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>
        
        <!-- Hiển thị Trạng Thái Tùy Chọn Nhãn Rủi Ro -->
        <div class="col-span-2 flex justify-end">
            ${getRiskBadge(record.risk_level, record.risk_level_vi)}
        </div>
    `;

    return row;
}

/**
 * Xem các thông điệp chi tiết của đối tượng mã chẩn đoán ID
 * @param {string} diagnosisId - Định danh ID chẩn đoán bệnh
 */
function viewDiagnosisDetail(diagnosisId) {
    navigateTo(`result.html?id=${diagnosisId}`, { diagnosisId });
}

/**
 * Cài đặt nhóm tập hợp nút bộ lọc Filter
 */
function setupFilters() {
    const filterButtons = document.querySelectorAll('[data-risk-filter]');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const filterValue = btn.getAttribute('data-risk-filter');

            // 1. Reset TẤT CẢ nút về trạng thái Inactive (Nền trắng, chữ xám)
            filterButtons.forEach(b => {
                // Gán chuỗi class đầy đủ cho trạng thái chưa chọn
                b.className = `px-4 py-2 rounded-lg bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-gray-200 dark:border-gray-700 text-sm font-medium whitespace-nowrap transition-colors hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer`;
            });

            // 2. Set nút ĐƯỢC BẤM về trạng thái Active (Nền Xanh #007fff, Chữ Trắng)
            // Dùng bg-[#007fff] để ép màu xanh hiển thị ngay lập tức
            btn.className = `px-4 py-2 rounded-lg bg-[#007fff] text-white text-sm font-medium whitespace-nowrap transition-colors shadow-sm ring-2 ring-[#007fff] ring-offset-1 dark:ring-offset-[#0f1923] cursor-default`;

            // 3. Thực hiện lọc dữ liệu
            applyFilter(filterValue);
        });
    });
}

/**
 * Kích hoạt hiệu ứng lọc kết quả mảng phụ thuộc theo hạng mục nguy hiểm rủi ro
 * @param {string} riskLevel - Cấp độ rủi ro muốn chọn lọc (hoặc giá trị ngầm định 'all')
 */
function applyFilter(riskLevel) {
    currentFilter = riskLevel;

    if (riskLevel === 'all') {
        filteredData = [...historyData];
    } else {
        filteredData = historyData.filter(record => record.risk_level === riskLevel);
    }

    displayHistory(filteredData);
}

/**
 * Thiết lập khả năng tìm kiếm cơ bản dựa trên văn bản
 */
function setupSearch() {
    const searchInput = document.querySelector('input[placeholder*="Search"], input[placeholder*="Tìm kiếm"]');

    if (!searchInput) return;

    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(() => {
            const query = e.target.value.toLowerCase().trim();

            if (!query) {
                applyFilter(currentFilter);
                return;
            }

            // Lọc theo tìm kiếm từ khóa khớp với nội dung chuẩn đoán ID và nhóm tên bệnh lý tiếng việt / tiếng anh
            filteredData = historyData.filter(record => {
                const matchId = record.diagnosis_id.toLowerCase().includes(query);
                const matchDisease = record.disease_name_vi.toLowerCase().includes(query);
                const matchClass = record.predicted_class.toLowerCase().includes(query);

                return matchId || matchDisease || matchClass;
            });

            displayHistory(filteredData);
        }, 300); // Debounce kỹ thuật trễ 300ms chống spam truy vấn (latency lag control)
    });
}

/**
 * Cập nhật thông tin số lượng trạng thái bảng thành phần (stats)
 * @param {Array} records - Toàn bộ record đã được gọi lấy về hệ thống
 */
function updateStats(records) {
    // Thống kê đếm con số cho loại phân loại rủi ro trên toàn bảng
    const stats = {
        high: 0,
        medium: 0,
        low: 0
    };

    records.forEach(record => {
        if (record.risk_level === 'high' || record.risk_level === 'very_high') {
            stats.high++;
        } else if (record.risk_level === 'medium') {
            stats.medium++;
        } else {
            stats.low++;
        }
    });

    console.log('History stats:', stats);
}

/**
 * Xử lý hàm cập nhật dòng con số cho biết đang mở bao nhiêu bản ghi
 * @param {number} showing - Mật độ lượng kết quả bộ lọc cho ra thẻ hiển thị
 * @param {number} total - Tổng toàn bộ quy mô tất cả các bản ghi y tế cá nhân
 */
function updateRecordCount(showing, total) {
    const countEl = document.querySelector('[data-record-count]') ||
        document.querySelector('p.text-xs.text-gray-500');

    if (countEl) {
        countEl.textContent = `Hiển thị ${showing} / ${total} kết quả`;
    }
}
