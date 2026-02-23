/**
 * Logic Của Trang Kết Quả
 * Hiển thị kết quả chẩn đoán cùng chi tiết phân tích
 */

// Nhập các biến từ medical-terms.js để đồng bộ hiển thị tên bệnh tiếng Việt
import { DISEASE_NAMES, RISK_LEVELS, MEDICAL_LOGO } from '../js/medical-terms.js';

/**
 * Dịch tên bệnh từ tiếng Anh sang tiếng Việt
 * @param {string} englishName - Tên bệnh theo chuẩn tiếng Anh
 * @returns {string} Trả về chữ tên bệnh qua tiếng Việt
 */
function translateDiseaseName(englishName) {
    if (!englishName) return '';

    const normalized = englishName.toLowerCase().trim().replace(/\s+/g, '_');
    return DISEASE_NAMES[normalized] || englishName;
}

/**
 * Dịch mức độ rủi ro từ tên tiếng Anh qua tiếng Việt
 * @param {string} riskLevel - Mức Cấp độ rủi ro tiếng Anh
 * @returns {string} Cấp độ rủi ro tên tiếng Việt
 */
function translateRiskLevel(riskLevel) {
    if (!riskLevel) return '';

    const normalized = riskLevel.toLowerCase().trim();
    return RISK_LEVELS[normalized] || riskLevel;
}

let currentDiagnosis = null;

// Khởi tạo hoạt động khi trình duyệt đã tải trang DOM xong
document.addEventListener('DOMContentLoaded', async function () {
    console.log('Result page initialized');

    await loadDiagnosisResult();
    setupResultActions();
    setupFeedback();
});

/**
 * Tải kết nối và hiển thị đáp án chẩn đoán bệnh lên giao diện
 */
async function loadDiagnosisResult() {
    try {
        // Cố gắng thử lấy từ dữ liệu navigation chuyển cảnh đẩy qua trước tiên
        const navState = getNavigationState();
        const diagnosisId = navState?.diagnosisId || new URLSearchParams(window.location.search).get('id');

        // Lấy tạm dự phòng ở cache localStorage (kết quả chuẩn đoán thực nghiệm sát sườn nhất)
        let diagnosis = retrieve('latestDiagnosis');

        // Nếu bắt được 1 ID thông số đặc biệt, sẽ fetch gọi kết nối từ nguồn API Server
        if (diagnosisId && (!diagnosis || diagnosis.diagnosis_id !== diagnosisId)) {
            showLoader('Đang tải kết quả...');

            try {
                diagnosis = await apiCall(
                    API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.DIAGNOSIS(diagnosisId)
                );
            } catch (error) {
                hideLoader();
                showError('Không tìm thấy kết quả chẩn đoán');
                return;
            }

            hideLoader();
        }

        if (!diagnosis) {
            showError('Không tìm thấy kết quả chẩn đoán');
            setTimeout(() => {
                window.location.href = 'intro.html';
            }, 2000);
            return;
        }

        currentDiagnosis = diagnosis;
        displayDiagnosisResult(diagnosis);

        // Auto-load biểu đồ biểu thị vùng nhận dạng nguồn bệnh (GradCAM heatmap)
        loadGradCAM(diagnosis);

    } catch (error) {
        console.error('Error loading diagnosis:', error);
        showError('Lỗi khi tải kết quả');
    }
}

/**
 * Gắn chuỗi kết quả chẩn đoán AI lên giao diện trang html
 * @param {object} diagnosis - Object Dữ liệu API trả về
 */
function displayDiagnosisResult(diagnosis) {
    console.log('Displaying diagnosis:', diagnosis);

    // Cập nhật mã chuỗi định danh xét nghiệm chẩn đoán ID
    updateElement('[data-diagnosis-id]', diagnosis.diagnosis_id);

    // Dịch ngữ và cập nhật thông tin tên bệnh lên màn hình hiển thị
    const diseaseNameVi = diagnosis.disease_name_vi || translateDiseaseName(diagnosis.disease_name || diagnosis.disease_name_en);
    const diseaseNameEn = diagnosis.disease_name_en || diagnosis.disease_name || '';

    updateElement('[data-disease-name]', diseaseNameVi);
    updateElement('[data-disease-name-en]', diseaseNameEn);

    // Cập nhật giá trị Độ Tự Tin Phần Trăm/Chính Xác dự đoán của Máy học (Confidence)
    updateElement('[data-confidence]', diagnosis.confidence_percent);
    updateElement('[data-confidence-value]', `${(diagnosis.confidence * 100).toFixed(1)}%`);

    // Cập nhật trạng thái vòng tròn % độ chính xác dạng trăng khuyết
    updateConfidenceProgress(diagnosis.confidence);

    // Dịch ngữ thông báo cảnh báo nguy hiểm (Risk Level)
    const riskLevelVi = diagnosis.risk_level_vi || translateRiskLevel(diagnosis.risk_level);
    updateRiskLevel(diagnosis.risk_level, riskLevelVi);

    // Cập nhật mục lời dặn của hệ thống (recommendations)
    updateRecommendations(diagnosis.recommendations);

    // Cập nhật dấu thời gian (cột mốc khám chẩn đoán thực tế mới tinh)
    updateElement('[data-timestamp]', formatDate(diagnosis.timestamp));

    // Cập nhật danh sách tất cả các chẩn đoán thuộc nhánh bệnh nguy cơ liên đới khác
    updateAllPredictions(diagnosis.all_predictions);

    // Kiểm tra trạng thái phản hồi để ẩn/hiện form
    const formContainer = document.getElementById('feedback-form');
    const successMsg = document.getElementById('feedback-success');
    if (formContainer && successMsg) {
        if (diagnosis.has_feedback) {
            formContainer.classList.add('hidden');
            successMsg.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Đánh giá của bạn đã được ghi nhận trước đó.';
            successMsg.classList.remove('hidden');
            successMsg.classList.add('flex');
        } else {
            formContainer.classList.remove('hidden');
            successMsg.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Cảm ơn bạn đã đóng góp! Phản hồi đã được ghi nhận.';
            successMsg.classList.add('hidden');
            successMsg.classList.remove('flex');
        }
    }

    // Hiển thị dải băng cảnh báo bệnh nguy hiểm (nếu có)
    const criticalBanner = document.getElementById('critical-warning-banner');
    const criticalText = document.getElementById('critical-warning-text');
    if (criticalBanner && criticalText) {
        if (diagnosis.critical_warning) {
            criticalText.textContent = `Dấu hiệu của ${diagnosis.critical_warning.name_vi} (${(diagnosis.critical_warning.confidence * 100).toFixed(1)}%)`;
            criticalBanner.classList.remove('hidden');
        } else {
            criticalBanner.classList.add('hidden');
        }
    }
}

/**
 * Cập nhật nội dung đối tượng element HTML trỏ qua CSS matcher
 * @param {string} selector - CSS selector trỏ mục tiêu html
 * @param {string} content - Nội dung đoạn text hiển thị mới
 */
function updateElement(selector, content) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        if (el) el.textContent = content;
    });
}

/**
 * Hàm cập nhật thành phần đồ họa (SVG) vòng tròn thể hiện độ chính xác %
 * @param {number} confidence - Thang tỷ lệ chẩn đoán chính xác (0-1)
 */
function updateConfidenceProgress(confidence) {
    const percent = confidence * 100;

    // Truy tìm thẻ nhẽ SVG Circle (vòng tròn khung rỗng)
    const circles = document.querySelectorAll('circle[stroke-dasharray]');
    circles.forEach(circle => {
        // Tính ra chỉ số stroke-dasharray % khuyết trên vòng tròn
        const circumference = 100; // Approximate
        const dashArray = `${percent}, ${circumference}`;
        circle.setAttribute('stroke-dasharray', dashArray);
    });

    // Cập nhật biến dạng Text dạng con số văn bản hiển thị phần trăm (%)
    const percentTexts = document.querySelectorAll('.text-primary, [data-confidence-percent]');
    percentTexts.forEach(text => {
        if (text.textContent.includes('%')) {
            text.textContent = `${percent.toFixed(0)}%`;
        }
    });
}

/**
 * Cập nhật phần khuếch trường cờ rủi ro / báo động (Risk Badge)
 * @param {string} riskLevel - Bộ mã cấp độ rủi ro (Risk code)
 * @param {string} riskLevelVi - Text dịch vụ qua chuẩn bản Việt Nam
 */
function updateRiskLevel(riskLevel, riskLevelVi) {
    const riskBadges = document.querySelectorAll('[data-risk-badge]');
    const badgeHTML = getRiskBadge(riskLevel, riskLevelVi);

    riskBadges.forEach(badge => {
        badge.innerHTML = badgeHTML;
    });

    // Update mục Cảnh báo bệnh nguy hiểm dạng text
    updateElement('[data-risk-level]', riskLevelVi);
}

/**
 * Hiển thị cập nhật thông tin tư vấn / lời khuyên của chuyên gia
 * @param {object} recommendations - Gói Đối tượng thông tin kèm theo báo cáo của bệnh
 */
function updateRecommendations(recommendations) {
    if (!recommendations) return;

    // Lên bài miêu tả chẩn đoán sơ bộ mô mô tả tình trạng
    updateElement('[data-recommendation-description]', recommendations.description);

    // Update độ nghiêm trọng (khẩn cấp phải xin can thiệp/điều trị)
    updateElement('[data-recommendation-urgency]', recommendations.urgency);

    // Sinh các bước mục Hành động gợi ý tư vấn dành cho nạn nhân / user
    const actionsList = document.querySelector('[data-recommendation-actions]');
    if (actionsList && recommendations.actions) {
        actionsList.innerHTML = recommendations.actions.map(action => `
            <li class="flex items-start gap-3">
                <span class="material-symbols-outlined text-primary text-lg mt-0.5">check_circle</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">${action}</span>
            </li>
        `).join('');
    }
}

/**
 * Danh sách Cập nhật tất cả các hạng mục chẩn đoán kèm theo phần trăm ước đoán xác suất
 * @param {object} predictions - Dictionary trả về bao chứa chẩn đoán class
 */
function updateAllPredictions(predictions) {
    const container = document.querySelector('[data-all-predictions]');
    if (!container || !predictions) return;

    // Chỉ có lấy đúng top 3 nhóm bệnh lậu đứng điểm chẩn bị mắc vào có tỉ lệ xác suất dự đoán (Confidence) đạt độ tin cậy mạnh nhất
    const topPredictions = Object.entries(predictions)
        .slice(0, 3)
        .map(([classCode, confidence]) => ({
            classCode,
            diseaseNameVi: translateDiseaseName(classCode),
            confidence,
            confidencePercent: (confidence * 100).toFixed(1)
        }));

    // Render gắn mã text String vào lại HTML element
    container.innerHTML = topPredictions.map(pred => `
        <div class="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">${pred.diseaseNameVi}</span>
            <div class="flex items-center gap-2 flex-1 mx-4">
                <div class="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div class="h-full bg-primary rounded-full" style="width: ${pred.confidencePercent}%"></div>
                </div>
                <span class="text-xs font-bold text-slate-600 dark:text-slate-400">${pred.confidencePercent}%</span>
            </div>
        </div>
    `).join('');
}

/**
 * Lắp các sự kiện cho bộ Nút hành động thao tác cho trang Kết Quả
 */
function setupResultActions() {
    // Thiết lập nút Lưu Dữ Liệu
    const saveBtn = document.querySelector('[data-save-btn]');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            showSuccess('Kết quả đã được lưu');
        });
    }

    // Nút in ấn lập báo cáo xuất tài liệu bệnh lý (Xuất PDF Report format)
    const printBtn = document.querySelector('[data-print-btn]');
    if (printBtn) {
        printBtn.addEventListener('click', async () => {
            try {
                // Bảo đảm rằng cả 2 thư viện hỗ trợ (html2canvas và jspdf) đều đã tải vào browser hoàn tất
                if (typeof html2canvas === 'undefined' || typeof window.jspdf === 'undefined') {
                    showError('Đang tải công cụ xuất PDF, vui lòng thử lại sau.');
                    return;
                }

                showLoader('Đang tạo báo cáo PDF...');
                const jsPDF = window.jspdf.jsPDF;

                // Nhắm chỉ định chính xác bao quát phân vùng cần in màn hình ở phạm vi 'main' html block component
                const elementToCapture = document.querySelector('main');

                // Ẩn tạm thời thanh Tác Vụ nút in ấn cũng như các khu vực thu form ý kiến người dùng (Feedback section) không đưa lên file PDF cho đẹp
                const actionBar = elementToCapture.querySelector('.sticky.bottom-4');
                const feedbackSection = elementToCapture.querySelector('#feedback-section');
                if (actionBar) actionBar.style.display = 'none';
                if (feedbackSection) feedbackSection.style.display = 'none';

                // Đảm bảo là Cụm biểu đồ ảnh nhiệt đánh dấu tổn thương (GradCAM Area) sẽ không nằm nửa trang trên nửa bị ngắt làm đôi (break-inside)
                const gradCamSection = elementToCapture.querySelector('#gradcam-section');
                if (gradCamSection) {
                    gradCamSection.style.breakInside = 'avoid';
                }

                // Thực hiện chụp ảnh bằng thiết bị màn hình (snapshot html to canvas buffer)
                const canvas = await html2canvas(elementToCapture, {
                    scale: 2, // Higher resolution
                    useCORS: true,
                    logging: false,
                    backgroundColor: document.documentElement.classList.contains('dark') ? '#0f1923' : '#f5f7f8'
                });

                // Thu hồi tính năng ẩn, trả lại màn hình web như cũ chờ người dùng quan sát tiếp
                if (actionBar) actionBar.style.display = '';
                if (feedbackSection) feedbackSection.style.display = '';

                // Tham số toán học tính chuẩn về bản in Giấy theo kích thước chuẩn khung giấy A4 dọc
                const imgWidth = 210; // A4 width in mm
                const pageHeight = 297; // A4 height in mm
                const imgHeight = canvas.height * imgWidth / canvas.width;
                let heightLeft = imgHeight;

                const pdf = new jsPDF('p', 'mm', 'a4');
                let position = 0;

                // Dán hình chụp buffer xuống trang thứ 1
                pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;

                // Nếu form HTML của user quá xá dài lê thê, tiến hành tạo ra nhiều dòng cắt giấy phân xuống nhiều Trang cho đến khi hết mảnh nội dung canvas
                while (heightLeft >= 0) {
                    position = heightLeft - imgHeight;
                    pdf.addPage();
                    pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, position, imgWidth, imgHeight);
                    heightLeft -= pageHeight;
                }

                pdf.save(`MedAI_BaoCao_${currentDiagnosis?.diagnosis_id || 'Chẩn_Đoán'}.pdf`);

                hideLoader();
                showSuccess('Đã xuất báo cáo PDF thành công');
            } catch (error) {
                hideLoader();
                console.error('PDF Export Error:', error);
                showError('Lỗi khi xuất PDF');
            }
        });
    }

    // Nút điều hướng hỗ trợ tra cứu bệnh viện mọc xung quanh chẩn đoán (Bản đồ tìm Clinic)
    const clinicBtn = document.querySelector('[data-clinic-btn]');
    if (clinicBtn) {
        clinicBtn.addEventListener('click', () => {
            showError('Chức năng tìm phòng khám đang được phát triển');
        });
    }
}

// ======== GradCAM ========

/**
 * Chạy xử lý hiển thị gọi API bản đồ nhiệt GradCAM mô tả mật độ nhận dạng tổn thương vùng do AI phân tách.
 * Biện pháp này sẽ nhờ truy van khôi phục lại tấm file Base64 image Gốc đang còn được cất tạm ở sessionStorage
 * @param {object} diagnosis - Lệnh danh sách thuộc đối tượng chẩn bệnh hiện tại
 */
async function loadGradCAM(diagnosis) {
    const loading = document.getElementById('gradcam-loading');
    const result = document.getElementById('gradcam-result');
    const errorEl = document.getElementById('gradcam-error');
    const heatmapImg = document.getElementById('gradcam-heatmap');
    const originalImg = document.getElementById('gradcam-original');
    const classLabel = document.getElementById('gradcam-class-label');

    if (!loading || !result || !errorEl) return;

    // Bật Loading vòng lập loading
    loading.classList.remove('hidden');
    result.classList.add('hidden');
    errorEl.classList.add('hidden');

    try {
        let file = null;
        let imageDataUrl = null;

        // 1. Cố tìm kiếm bốc lại bức tấm ảnh gốc của người dùng được lưu trong ngăn Session hồi đầu upload
        imageDataUrl = sessionStorage.getItem(`recentImage_${diagnosis.diagnosis_id}`);

        if (imageDataUrl) {
            // Thay đổi kiểu chuỗi dataURL base64 → ra Blob memory → đẩy về File system ảo
            const blob = dataURLtoBlob(imageDataUrl);
            file = new File([blob], 'image.jpg', { type: blob.type });
        } else if (diagnosis.image_filename) {
            // 2. Chế độ Xem Lịch Sử (History Mode): Download ảnh gốc từ Server backend
            const imageUrl = API_CONFIG.BASE_URL.replace('/api/v1', '') + '/uploads/' + diagnosis.image_filename;
            const res = await fetch(imageUrl);
            if (!res.ok) throw new Error('Không thể tải ảnh gốc cũ từ lịch sử');
            const blob = await res.blob();
            file = new File([blob], diagnosis.image_filename, { type: blob.type });

            // Xây dựng dataUrl để chèn hiển thị ảnh gốc trong thẻ <img> phía dưới
            imageDataUrl = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            });
        } else {
            throw new Error('Không có hình ảnh để vẽ GradCAM');
        }

        // Thi công truyền nạp bộ FormData API payload request
        const formData = new FormData();
        formData.append('file', file);
        if (diagnosis.predicted_class) {
            formData.append('target_class', diagnosis.predicted_class);
        }

        // Chạy gọi apiCall (có bao gồm token đăng nhập nếu có)
        const url = API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.GRADCAM;
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            // Thêm Authorization header nếu cần thiết (dù GradCAM endpoint hiện tại có thể không yêu cầu)
            headers: localStorage.getItem('access_token') ? {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            } : {}
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        // Nhận lại và đắp thành phẩm xuất màn ảnh Giao Tiếp UI (Kết quả)
        heatmapImg.src = data.heatmap_overlay;
        originalImg.src = imageDataUrl;
        if (classLabel) classLabel.textContent = data.predicted_class;

        loading.classList.add('hidden');
        result.classList.remove('hidden');

    } catch (err) {
        console.warn('GradCAM error:', err.message);
        loading.classList.add('hidden');
        errorEl.classList.remove('hidden');
        errorEl.classList.add('flex');
    }
}

/**
 * Bộ công cụ chuyển định dạng base64 chuỗi URI thành ra dạng tệp ảo Blob.
 * @param {string} dataURL
 * @returns {Blob}
 */
function dataURLtoBlob(dataURL) {
    const [header, base64] = dataURL.split(',');
    const mime = header.match(/:(.*?);/)[1];
    const binary = atob(base64);
    const array = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
    return new Blob([array], { type: mime });
}

/**
 * Gắn kết cho chuỗi các sự kiện nhấp tương tác dành riêng về tính năng Đánh Giá Mô Hình / Feedback Phản Biên Hệ Thống
 */
function setupFeedback() {
    const btnCorrect = document.getElementById('btn-feedback-correct');
    const btnIncorrect = document.getElementById('btn-feedback-incorrect');
    const incorrectDetails = document.getElementById('feedback-incorrect-details');
    const selectActualClass = document.getElementById('feedback-actual-class');
    const submitBtn = document.getElementById('btn-submit-feedback');
    const formContainer = document.getElementById('feedback-form');
    const successMsg = document.getElementById('feedback-success');
    const notesInput = document.getElementById('feedback-notes');

    if (!btnCorrect) return; // Nhanh chóng tuýt còi thoát script do ta có khả năng k nằm trên site result.html

    // Đổ danh sách đổ option mảng option tên bệnh (điền Select menu thả xuống class thực tế)
    Object.keys(DISEASE_NAMES).forEach(code => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = DISEASE_NAMES[code];
        selectActualClass.appendChild(option);
    });

    // Tác vụ cho Giao diện - User bấm nút Xác nhận 'Chẩn Đoán Chuẩn\Đúng'
    btnCorrect.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log("Feedback: Clicked Correct");
        await submitFeedback(true);
    });

    // Tác vụ nút 'Chẩn Đoán SAI' (nút bấm trỏ mở form input cho việc User tự chọn nhập lại Class/bệnh lý đúng thực tế nhất)
    btnIncorrect.addEventListener('click', (e) => {
        e.preventDefault();
        console.log("Feedback: Clicked Incorrect");
        incorrectDetails.classList.remove('hidden');
        incorrectDetails.classList.add('flex');
    });

    // Ấn phím Submit cho báo cáo "feedback CHẨN ĐOÁN SAI - Yêu cầu AI học lại" qua API.
    submitBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log("Feedback: Clicked Submit Incorrect");
        const actualClass = selectActualClass.value;
        if (!actualClass) {
            showError('Vui lòng chọn bệnh thực sự');
            return;
        }
        await submitFeedback(false, actualClass, notesInput.value);
    });

    async function submitFeedback(isCorrect, actualClass = null, notes = null) {
        if (!currentDiagnosis || !currentDiagnosis.diagnosis_id) {
            showError('Lỗi dữ liệu chẩn đoán');
            return;
        }

        try {
            showLoader('Đang gửi phản hồi...');
            const payload = {
                diagnosis_id: currentDiagnosis.diagnosis_id,
                is_correct: isCorrect,
                actual_class: actualClass,
                notes: notes
            };

            await apiCall(API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.FEEDBACK, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            hideLoader();
            // Sau thành công hãy Ẩn rấp form phản hồi, hiện thông báo text báo cảm tạ User
            formContainer.classList.add('hidden');
            successMsg.classList.remove('hidden');
            successMsg.classList.add('flex');
        } catch (error) {
            hideLoader();
            console.error('Feedback error:', error);
            showError('Không thể gửi phản hồi. Vui lòng thử lại.');
        }
    }
}
