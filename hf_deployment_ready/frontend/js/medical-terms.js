/**
 * Từ Điển Thuật Ngữ Y Khoa
 * Nơi tập trung các bản dịch tiếng Việt cho các thuật ngữ y học
 * Sử dụng các hằng số này trên toàn trang ứng dụng để tiện đồng bộ
 * 
 * Cập nhật: Toàn bộ 24 danh mục phân loại bệnh với form Tiếng Việt (Tiếng Anh)
 */

// Biểu tượng Y tế
export const MEDICAL_LOGO = '🏥';

// Tên Bệnh / Kết Cấu Chẩn Đoán (Tất cả 24 loại bệnh)
export const DISEASE_NAMES = {
    'acne_rosacea': 'Mụn trứng cá & Rosacea (Acne Rosacea)',
    'actinic_keratosis': 'Dày sừng quang hóa - Tiền ung thư (Actinic Keratosis)',
    'alopecia_hair_loss': 'Rụng tóc & Bệnh về tóc (Alopecia Hair Loss)',
    'basal_cell_carcinoma': 'Ung thư tế bào đáy (Basal Cell Carcinoma)',
    'bullous_disease_pemphigus': 'Bệnh bóng nước (Bullous Disease Pemphigus)',
    'cellulitis_impetigo': 'Viêm mô tế bào & Chốc lở (Cellulitis Impetigo)',
    'contact_dermatitis': 'Viêm da tiếp xúc - Dị ứng (Contact Dermatitis)',
    'dermatofibroma': 'U xơ da lành tính (Dermatofibroma)',
    'eczema_atopic_dermatitis': 'Chàm & Viêm da cơ địa (Eczema Atopic Dermatitis)',
    'exanthems_drug_eruptions': 'Phát ban do thuốc (Exanthems Drug Eruptions)',
    'fungal_infections': 'Nấm da - Hắc lào, Nấm móng (Fungal Infections)',
    'infestations_bites': 'Ký sinh trùng & Côn trùng cắn (Infestations Bites)',
    'lupus_connective_tissue': 'Lupus ban đỏ & Bệnh mô liên kết (Lupus Connective Tissue)',
    'melanocytic_nevus': 'Nốt ruồi lành tính (Melanocytic Nevus)',
    'melanoma': 'Ung thư hắc tố (Melanoma)',
    'pigmentation_disorders': 'Rối loạn sắc tố (Pigmentation Disorders)',
    'psoriasis_lichen_planus': 'Vảy nến & Lichen phẳng (Psoriasis Lichen Planus)',
    'seborrheic_keratosis': 'Dày sừng tiết bã & U lành tính (Seborrheic Keratosis)',
    'squamous_cell_carcinoma': 'Ung thư tế bào vảy (Squamous Cell Carcinoma)',
    'systemic_disease': 'Biểu hiện da của bệnh nội khoa (Systemic Disease)',
    'urticaria_hives': 'Mề đay (Urticaria Hives)',
    'vascular_lesion': 'Tổn thương mạch máu & U mạch (Vascular Lesion)',
    'vasculitis': 'Viêm mạch máu (Vasculitis)',
    'viral_infections': 'Nhiễm trùng virus - Mụn cóc (Viral Infections)'
};

// Các cấp độ rủi ro
export const RISK_LEVELS = {
    'critical': 'Nguy hiểm',
    'very_high': 'Rất cao',
    'high': 'Cao',
    'medium': 'Trung bình',
    'low': 'Thấp',
};

// Các thuật ngữ Y tế
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

// Nhãn giao diện UI
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

// Khuyến nghị dựa theo mức độ Rủi ro
export const RECOMMENDATIONS = {
    'critical': {
        title: 'Cần khẩn cấp',
        description: 'Vui lòng liên hệ bác sĩ da liễu ngay lập tức để được tư vấn và có thể cần sinh thiết.',
    },
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

// Các thông báo lỗi
export const ERROR_MESSAGES = {
    'upload_failed': 'Tải ảnh lên thất bại. Vui lòng thử lại.',
    'analysis_failed': 'Phân tích thất bại. Vui lòng thử lại.',
    'network_error': 'Lỗi kết nối. Vui lòng kiểm tra kết nối mạng.',
    'invalid_file': 'File không hợp lệ. Chỉ chấp nhận JPG, PNG, HEIC.',
    'file_too_large': 'File quá lớn. Kích thước tối đa 10MB.',
    'server_error': 'Lỗi máy chủ. Vui lòng thử lại sau.',
};

// Các thông báo thành công
export const SUCCESS_MESSAGES = {
    'upload_success': 'Tải ảnh lên thành công!',
    'analysis_complete': 'Phân tích hoàn tất!',
    'saved': 'Đã lưu thành công!',
};

/**
 * Các hàm hỗ trợ / bổ trợ (Helpers Func)
 */

/**
 * Dịch tên bệnh chẩn đoán sang tiếng Việt
 * @param {string} diseaseCode - Nhóm Mã bệnh từ API
 * @returns {string} Trả về tên bệnh bằng Tiếng Việt đi kèm ngoặc đơn tiếng Anh
 */
export function translateDiseaseName(diseaseCode) {
    const code = diseaseCode.toLowerCase().replace(/\s+/g, '_');
    return DISEASE_NAMES[code] || diseaseCode;
}

/**
 * Dịch danh mục đánh giá mức độ rủi ro sang tiếng Việt
 * @param {string} riskLevel - Cấp độ bị ảnh hưởng từ API
 * @returns {string} Cấp độ rủi ro theo Tiếng Việt
 */
export function translateRiskLevel(riskLevel) {
    const level = riskLevel.toLowerCase();
    return RISK_LEVELS[level] || riskLevel;
}

/**
 * Nhận lời khuyên đánh giá dựa trên mức độ rủi ro
 * @param {string} riskLevel - Cấp độ rủi ro
 * @returns {object} Trả về Đối tượng Khuyến nghị gồm có title(tiêu đề) và description(mô tả phân tích)
 */
export function getRecommendation(riskLevel) {
    const level = riskLevel.toLowerCase();
    return RECOMMENDATIONS[level] || RECOMMENDATIONS['medium'];
}

/**
 * Dịch từ vựng cụm thuật ngữ biểu nghĩa Y khoa sang Tiếng Việt
 * @param {string} term - Thuật ngữ Y khoa
 * @returns {string} Bản dịch hoàn chỉnh
 */
export function translateMedicalTerm(term) {
    const normalizedTerm = term.toLowerCase().replace(/\s+/g, '_');
    return MEDICAL_TERMS[normalizedTerm] || term;
}
