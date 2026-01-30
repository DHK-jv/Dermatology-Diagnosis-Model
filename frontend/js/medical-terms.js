/**
 * Medical Terminology Dictionary
 * Centralized Vietnamese translations for medical terms
 * Use these constants throughout the application for consistency
 */

// Disease Names / Diagnosis
export const DISEASE_NAMES = {
    'melanoma': 'Ung thư hắc tố',
    'nevus': 'Nốt ruồi lành tính',
    'basal_cell_carcinoma': 'Ung thư tế bào đáy',
    'actinic_keratosis': 'Sừng hóa quang tuyến',
    'benign_keratosis': 'Sừng hóa lành tính',
    'dermatofibroma': 'U xơ da',
    'vascular_lesion': 'Tổn thương mạch máu',
    'squamous_cell_carcinoma': 'Ung thư tế bào vảy',
};

// Risk Levels
export const RISK_LEVELS = {
    'very_high': 'Rất cao',
    'high': 'Cao',
    'medium': 'Trung bình',
    'low': 'Thấp',
};

// Medical Terms
export const MEDICAL_TERMS = {
    'confidence': 'Độ tin cậy',
    'lesion': 'Vùng tổn thương',
    'screening': 'Sàng lọc',
    'assessment': 'Đánh giá',
    'biopsy': 'Sinh thiết',
    'diagnosis': 'Chẩn đoán',
    'recommendation': 'Khuyến nghị',
    'consultation': 'Tư vấn',
    'dermatologist': 'Bác sĩ da liễu',
    'analysis': 'Phân tích',
    'result': 'Kết quả',
    'history': 'Lịch sử',
    'upload': 'Tải lên',
    'image': 'Hình ảnh',
    'patient': 'Bệnh nhân',
};

// UI Labels
export const UI_LABELS = {
    'high_risk': 'Nguy cơ cao',
    'medium_risk': 'Nguy cơ trung bình',
    'low_risk': 'Nguy cơ thấp',
    'no_risk': 'Không có nguy cơ',
    'view_details': 'Xem chi tiết',
    'back': 'Quay lại',
    'next': 'Tiếp theo',
    'cancel': 'Hủy',
    'confirm': 'Xác nhận',
    'upload_image': 'Tải ảnh lên',
    'analyze': 'Phân tích',
    'loading': 'Đang tải',
    'processing': 'Đang xử lý',
    'complete': 'Hoàn tất',
    'error': 'Lỗi',
    'success': 'Thành công',
};

// Recommendations by Risk Level
export const RECOMMENDATIONS = {
    'very_high': {
        title: 'Cần khẩn cấp',
        description: 'Vui lòng liên hệ bác sĩ da liễu ngay lập tức để được tư vấn và có thể cần sinh thiết.',
    },
    'high': {
        title: 'Cần thăm khám',
        description: 'Khuyến nghị đặt lịch hẹn với bác sĩ da liễu trong vòng 1-2 tuần.',
    },
    'medium': {
        title: 'Theo dõi',
        description: 'Nên theo dõi vùng tổn thương và tái khám nếu có thay đổi về hình dạng, màu sắc hoặc kích thước.',
    },
    'low': {
        title: 'Lành tính',
        description: 'Tổn thương có vẻ lành tính. Tiếp tục theo dõi định kỳ và thăm khám nếu có thay đổi.',
    },
};

// Error Messages
export const ERROR_MESSAGES = {
    'upload_failed': 'Tải ảnh lên thất bại. Vui lòng thử lại.',
    'analysis_failed': 'Phân tích thất bại. Vui lòng thử lại.',
    'network_error': 'Lỗi kết nối. Vui lòng kiểm tra kết nối mạng.',
    'invalid_file': 'File không hợp lệ. Chỉ chấp nhận JPG, PNG, HEIC.',
    'file_too_large': 'File quá lớn. Kích thước tối đa 10MB.',
    'server_error': 'Lỗi máy chủ. Vui lòng thử lại sau.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
    'upload_success': 'Tải ảnh lên thành công!',
    'analysis_complete': 'Phân tích hoàn tất!',
    'saved': 'Đã lưu thành công!',
};

/**
 * Helper Functions
 */

/**
 * Translate disease name to Vietnamese
 * @param {string} diseaseCode - Disease code from API
 * @returns {string} Vietnamese disease name
 */
export function translateDiseaseName(diseaseCode) {
    const code = diseaseCode.toLowerCase().replace(/\s+/g, '_');
    return DISEASE_NAMES[code] || diseaseCode;
}

/**
 * Translate risk level to Vietnamese
 * @param {string} riskLevel - Risk level from API
 * @returns {string} Vietnamese risk level
 */
export function translateRiskLevel(riskLevel) {
    const level = riskLevel.toLowerCase();
    return RISK_LEVELS[level] || riskLevel;
}

/**
 * Get recommendation by risk level
 * @param {string} riskLevel - Risk level
 * @returns {object} Recommendation object with title and description
 */
export function getRecommendation(riskLevel) {
    const level = riskLevel.toLowerCase();
    return RECOMMENDATIONS[level] || RECOMMENDATIONS['medium'];
}

/**
 * Translate medical term to Vietnamese
 * @param {string} term - Medical term
 * @returns {string} Vietnamese translation
 */
export function translateMedicalTerm(term) {
    const normalizedTerm = term.toLowerCase().replace(/\s+/g, '_');
    return MEDICAL_TERMS[normalizedTerm] || term;
}
