/**
 * History Page Logic
 * Fetch and display diagnosis history from API
 */

let historyData = [];
let filteredData = [];
let currentFilter = 'all';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function () {
    console.log('History page initialized');

    await loadHistory();
    setupFilters();
    setupSearch();
});

/**
 * Load history from API
 */
async function loadHistory() {
    try {
        // --- 1. SET LOADING STATE ---
        const loadingState = document.getElementById('loading-state');
        const historyTable = document.getElementById('history-table');
        const emptyState = document.getElementById('empty-state');
        const tableBody = document.getElementById('history-records');

        // Show inline loader, hide others
        if (loadingState) loadingState.classList.remove('hidden');
        if (historyTable) historyTable.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');

        // Also show global loader for feedback
        showLoader('Đang tải lịch sử...');

        // --- 2. FETCH DATA ---
        const response = await apiCall(
            API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.HISTORY + '?limit=100'
        );

        // --- 3. HANDLE RESPONSE ---
        if (response && response.records) {
            historyData = response.records;
            filteredData = [...historyData];

            if (response.records.length > 0) {
                // HAS DATA: Show table
                if (historyTable) historyTable.classList.remove('hidden');
                displayHistory(filteredData);
            } else {
                // NO DATA: Show empty state
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
        // On error, show empty state or keep previous specific logic
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.classList.remove('hidden');

    } finally {
        // --- 4. CLEANUP (ALWAYS RUNS) ---
        // Always hide the loaders
        const loadingState = document.getElementById('loading-state');
        if (loadingState) loadingState.classList.add('hidden');
        hideLoader(); // Hide global loader
    }
}

/**
 * Display history records in table
 * @param {Array} records - History records
 */
function displayHistory(records) {
    const tableBody = document.getElementById('history-records');

    if (!tableBody) {
        console.error('History table container not found');
        return;
    }

    // Clear existing rows
    const rows = tableBody.querySelectorAll('.bg-white, .bg-gray-900');
    rows.forEach(row => row.remove());

    if (records.length === 0) {
        // Show empty state
        tableBody.innerHTML += `
            <div class="col-span-12 text-center py-12">
                <span class="material-symbols-outlined text-6xl text-gray-300 dark:text-gray-600">folder_open</span>
                <p class="text-gray-500 dark:text-gray-400 mt-4">Không có dữ liệu</p>
            </div>
        `;
        return;
    }

    // Generate rows
    records.forEach(record => {
        const row = createHistoryRow(record);
        tableBody.appendChild(row);
    });

    // Update count
    updateRecordCount(records.length, historyData.length);
}

/**
 * Create a history table row
 * @param {object} record - Diagnosis record
 * @returns {HTMLElement} Row element
 */
function createHistoryRow(record) {
    const row = document.createElement('div');
    row.className = 'bg-white dark:bg-gray-900 px-6 py-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow grid grid-cols-12 gap-4 items-center cursor-pointer';

    // Click to view details
    row.addEventListener('click', () => {
        viewDiagnosisDetail(record.diagnosis_id);
    });

    // Generate initials for avatar
    const parts = record.diagnosis_id.split('-');
    const initials = parts.length > 2 ? parts[2].substring(0, 2).toUpperCase() : 'DG';

    // Risk color
    const riskColors = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'red',
        'very_high': 'red'
    };
    const riskColor = riskColors[record.risk_level] || 'yellow';

    row.innerHTML = `
        <!-- Patient/ID Info -->
        <div class="col-span-4 flex items-center gap-3">
            <div class="h-10 w-10 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-primary font-bold">
                ${initials}
            </div>
            <div class="flex flex-col">
                <span class="font-bold text-[#111817] dark:text-white">${record.diagnosis_id}</span>
                <span class="text-xs text-gray-500">${formatDateShort(record.timestamp)}</span>
            </div>
        </div>
        
        <!-- Lesion Preview -->
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
        
        <!-- Diagnosis -->
        <div class="col-span-2">
            <span class="px-2.5 py-1 rounded bg-${riskColor}-100 dark:bg-${riskColor}-900/30 text-${riskColor}-600 dark:text-${riskColor}-400 text-xs font-bold">
                ${record.disease_name_vi}
            </span>
        </div>
        
        <!-- Confidence -->
        <div class="col-span-2">
            <div class="flex items-center gap-2">
                <div class="w-full bg-gray-100 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-${riskColor}-500 h-full rounded-full" style="width: ${(record.confidence * 100).toFixed(0)}%"></div>
                </div>
                <span class="text-xs font-bold text-gray-700 dark:text-gray-300">${(record.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>
        
        <!-- Risk Level -->
        <div class="col-span-2 flex justify-end">
            ${getRiskBadge(record.risk_level, record.risk_level_vi)}
        </div>
    `;

    return row;
}

/**
 * View diagnosis detail
 * @param {string} diagnosisId - Diagnosis ID
 */
function viewDiagnosisDetail(diagnosisId) {
    navigateTo(`result.html?id=${diagnosisId}`, { diagnosisId });
}

/**
 * Setup filter buttons
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
 * Apply risk level filter
 * @param {string} riskLevel - Risk level to filter (or 'all')
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
 * Setup search functionality
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

            // Search in diagnosis ID and disease name
            filteredData = historyData.filter(record => {
                const matchId = record.diagnosis_id.toLowerCase().includes(query);
                const matchDisease = record.disease_name_vi.toLowerCase().includes(query);
                const matchClass = record.predicted_class.toLowerCase().includes(query);

                return matchId || matchDisease || matchClass;
            });

            displayHistory(filteredData);
        }, 300); // Debounce 300ms
    });
}

/**
 * Update statistics/counts
 * @param {Array} records - All records
 */
function updateStats(records) {
    // Count by risk level
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
 * Update record count display
 * @param {number} showing - Number of records showing
 * @param {number} total - Total number of records
 */
function updateRecordCount(showing, total) {
    const countEl = document.querySelector('[data-record-count]') ||
        document.querySelector('p.text-xs.text-gray-500');

    if (countEl) {
        countEl.textContent = `Hiển thị ${showing} / ${total} kết quả`;
    }
}
