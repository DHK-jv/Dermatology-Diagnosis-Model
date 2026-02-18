"""
Constants and disease information mappings
"""

# Class names from model training (in order of model output)
# Standardized Dermnet NZ classes (24 classes)
# Optimized Class List (Merged and Cleaned)
CLASS_NAMES = [
    'acne_rosacea', 'actinic_keratosis', 'alopecia_hair_loss', 'basal_cell_carcinoma',
    'bullous_disease_pemphigus', 'cellulitis_impetigo', 'contact_dermatitis', 'dermatofibroma',
    'eczema_atopic_dermatitis', 'exanthems_drug_eruptions', 'fungal_infections',
    'infestations_bites', 'lupus_connective_tissue', 'melanocytic_nevus', 'melanoma',
    'pigmentation_disorders', 'psoriasis_lichen_planus', 'seborrheic_keratosis',
    'squamous_cell_carcinoma', 'systemic_disease', 'urticaria_hives', 'vascular_lesion',
    'vasculitis', 'viral_infections'
]

# Vietnamese disease names mapping (with English in parentheses)
DISEASE_NAMES_VI = {
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
}

# Medical logo emoji for system-wide use
MEDICAL_LOGO = '🏥'

# English disease names (for reference)
DISEASE_NAMES_EN = {k: k.replace('_', ' ').title() for k in CLASS_NAMES}

# Risk levels for all 24 disease classes
RISK_LEVELS = {
    'acne_rosacea': 'low',
    'actinic_keratosis': 'medium',  # Pre-cancer
    'alopecia_hair_loss': 'low',
    'basal_cell_carcinoma': 'high',  # Cancer
    'bullous_disease_pemphigus': 'medium',
    'cellulitis_impetigo': 'medium',
    'contact_dermatitis': 'low',
    'dermatofibroma': 'low',
    'eczema_atopic_dermatitis': 'low',
    'exanthems_drug_eruptions': 'medium',
    'fungal_infections': 'low',
    'infestations_bites': 'low',
    'lupus_connective_tissue': 'high',  # Autoimmune serious
    'melanocytic_nevus': 'low',
    'melanoma': 'critical',  # Deadly Cancer
    'pigmentation_disorders': 'low',
    'psoriasis_lichen_planus': 'medium',
    'seborrheic_keratosis': 'low',
    'squamous_cell_carcinoma': 'high',  # Cancer
    'systemic_disease': 'high',
    'urticaria_hives': 'low',
    'vascular_lesion': 'medium',
    'vasculitis': 'high',
    'viral_infections': 'low'
}

# Risk level Vietnamese translations
RISK_LEVEL_VI = {
    'low': 'Thấp',
    'medium': 'Trung bình',
    'high': 'Cao',
    'very_high': 'Rất cao',
    'critical': 'Nguy hiểm'
}

# Medical recommendations in Vietnamese for all 24 disease classes
RECOMMENDATIONS = {
    'acne_rosacea': 'Duy trì vệ sinh da mặt, hạn chế đồ cay nóng. Sử dụng sữa rửa mặt dịu nhẹ.',
    'actinic_keratosis': '⚠️ Tổn thương tiền ung thư. Nên theo dõi và điều trị để tránh tiến triển thành ung thư da.',
    'alopecia_hair_loss': 'Bổ sung vitamin, tránh căng thẳng. Đi khám nếu rụng tóc từng mảng hoặc đột ngột.',
    'basal_cell_carcinoma': '⚠️ CẢNH BÁO: Nghi ngờ ung thư tế bào đáy. Cần khám chuyên khoa ung bướu/da liễu ngay.',
    'bullous_disease_pemphigus': 'Tránh làm vỡ bọng nước để ngừa nhiễm trùng. Cần khám bác sĩ da liễu.',
    'cellulitis_impetigo': 'Giữ vệ sinh vùng da bị nhiễm, có thể cần dùng kháng sinh theo chỉ định bác sĩ.',
    'contact_dermatitis': 'Tránh tiếp xúc với tác nhân gây dị ứng. Dùng kem dưỡng ẩm và thuốc bôi kháng viêm.',
    'dermatofibroma': 'U lành tính, thường không cần can thiệp trừ khi gây khó chịu hoặc thẩm mỹ.',
    'eczema_atopic_dermatitis': 'Dưỡng ẩm thường xuyên, tránh xà phòng tẩy rửa mạnh. Kiểm soát ngứa ngáy.',
    'exanthems_drug_eruptions': '⚠️ Ngưng thuốc nghi ngờ gây dị ứng ngay. Đi cấp cứu nếu khó thở hoặc phù mặt.',
    'fungal_infections': 'Giữ da khô thoáng, dùng thuốc bôi chống nấm. Điều trị đầy đủ để tránh tái phát.',
    'infestations_bites': 'Vệ sinh môi trường sống. Dùng thuốc bôi làm dịu da và chống ngứa.',
    'lupus_connective_tissue': '⚠️ Bệnh tự miễn nghiêm trọng cần theo dõi lâu dài bởi bác sĩ chuyên khoa.',
    'melanocytic_nevus': 'Nốt ruồi lành tính. Theo dõi nếu có thay đổi về hình dạng, màu sắc hoặc kích thước.',
    'melanoma': '🚨 NGUY HIỂM: Có dấu hiệu ung thư hắc tố. Cần đi khám và sinh thiết ngay lập tức!',
    'pigmentation_disorders': 'Dùng kem chống nắng SPF cao, các sản phẩm làm sáng da an toàn theo chỉ định.',
    'psoriasis_lichen_planus': 'Kiểm soát stress, dưỡng ẩm sâu. Có thể cần điều trị quang trị liệu hoặc thuốc toàn thân.',
    'seborrheic_keratosis': 'U lành tính do lão hóa. Có thể loại bỏ bằng phương pháp thẩm mỹ nếu muốn.',
    'squamous_cell_carcinoma': '⚠️ CẢNH BÁO: Nghi ngờ ung thư tế bào vảy. Cần can thiệp và điều trị sớm.',
    'systemic_disease': 'Biểu hiện da của bệnh nội khoa. Cần khám tổng quát để tìm nguyên nhân.',
    'urticaria_hives': 'Tránh tác nhân dị ứng (thức ăn, thời tiết, thuốc). Dùng thuốc chống dị ứng.',
    'vascular_lesion': 'Theo dõi sự phát triển. Có thể can thiệp laser hoặc phẫu thuật nếu cần.',
    'vasculitis': 'Nghỉ ngơi, nâng cao chân. Cần khám để xác định nguyên nhân và điều trị phù hợp.',
    'viral_infections': 'Tăng cường sức đề kháng. Tránh cạy nặn mụn cóc, có thể cần điều trị laser.'
}

# Color codes for risk levels (for frontend)
RISK_COLORS = {
    'low': '#10b981',      # green
    'medium': '#f59e0b',   # yellow/orange
    'high': '#ef4444',     # red
    'very_high': '#dc2626' # dark red
}
