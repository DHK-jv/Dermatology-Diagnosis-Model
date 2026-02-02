"""
Constants and disease information mappings
"""

# Class names from model training (in order of model output)
# Class names from model training (in order of model output)
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'scc', 'vasc']

# Vietnamese disease names mapping
DISEASE_NAMES_VI = {
    'akiec': 'Ung thư biểu mô tế bào gai',
    'bcc': 'Ung thư tế bào đáy',
    'bkl': 'Sừng hóa lành tính',
    'df': 'U xơ sợi da',
    'mel': 'Ung thư hắc tố (Melanoma)',
    'nv': 'Nốt ruồi lành tính',
    'scc': 'Ung thư biểu mô tế bào vảy',
    'vasc': 'Tổn thương mạch máu'
}

# English disease names (for reference)
DISEASE_NAMES_EN = {
    'akiec': 'Actinic Keratoses',
    'bcc': 'Basal Cell Carcinoma',
    'bkl': 'Benign Keratosis',
    'df': 'Dermatofibroma',
    'mel': 'Melanoma',
    'nv': 'Melanocytic Nevus',
    'scc': 'Squamous Cell Carcinoma',
    'vasc': 'Vascular Lesions'
}

# Risk levels
RISK_LEVELS = {
    'akiec': 'high',
    'bcc': 'high',
    'bkl': 'low',
    'df': 'low',
    'mel': 'very_high',
    'nv': 'low',
    'scc': 'high',
    'vasc': 'medium'
}

# Risk level translations
RISK_LEVEL_VI = {
    'low': 'Thấp',
    'medium': 'Trung bình',
    'high': 'Cao',
    'very_high': 'Rất cao'
}

# Medical recommendations in Vietnamese
RECOMMENDATIONS = {
    'akiec': {
        'description': 'Ung thư biểu mô tế bào gai là tổn thương tiền ung thư trên da có thể phát triển thành ung thư da.',
        'actions': [
            'Khám bác sĩ da liễu trong vòng 1-2 tuần',
            'Có thể cần sinh thiết để xác định chẩn đoán',
            'Tránh tiếp xúc với tia UV mạnh',
            'Không tự điều trị tại nhà'
        ],
        'urgency': 'Cần khám sớm'
    },
    'bcc': {
        'description': 'Ung thư tế bào đáy là loại ung thư da phổ biến nhất, thường lành tính nhưng cần điều trị.',
        'actions': [
            'Khám bác sĩ da liễu ngay trong tuần này',
            'Cần sinh thiết để xác nhận chẩn đoán',
            'Có thể cần phẫu thuật hoặc điều trị laser',
            'Theo dõi sự thay đổi của vùng da hàng ngày'
        ],
        'urgency': 'Cần khám khẩn'
    },
    'bkl': {
        'description': 'Sừng hóa lành tính là tổn thương da không nguy hiểm, thường gặp ở người lớn tuổi.',
        'actions': [
            'Khám định kỳ để theo dõi',
            'Không cần điều trị nếu không gây khó chịu',
            'Có thể loại bỏ vì mục đích thẩm mỹ',
            'Tránh cào gãi vùng da'
        ],
        'urgency': 'Không cấp thiết'
    },
    'df': {
        'description': 'U xơ sợi da là khối u lành tính, thường xuất hiện ở chi dưới.',
        'actions': [
            'Khám bác sĩ để xác nhận chẩn đoán',
            'Thường không cần điều trị',
            'Có thể loại bỏ bằng phẫu thuật nếu muốn',
            'Theo dõi nếu có thay đổi kích thước hoặc màu sắc'
        ],
        'urgency': 'Không cấp thiết'
    },
    'mel': {
        'description': 'Melanoma là loại ung thư da nguy hiểm nhất, có khả năng di căn cao nếu không phát hiện sớm.',
        'actions': [
            'KHẨN CẤP: Khám bác sĩ da liễu ngay lập tức',
            'Cần sinh thiết và xét nghiệm càng sớm càng tốt',
            'Tránh chạm vào, cào gãi vùng da',
            'Ghi nhận mọi thay đổi về kích thước, màu sắc hàng ngày',
            'Không tự điều trị hoặc loại bỏ'
        ],
        'urgency': 'KHẨN CẤP - Khám ngay'
    },
    'nv': {
        'description': 'Nốt ruồi lành tính là tổn thương da rất phổ biến và thường không nguy hiểm.',
        'actions': [
            'Theo dõi thường xuyên về thay đổi hình dạng, màu sắc',
            'Khám định kỳ hàng năm',
            'Bảo vệ da khỏi ánh nắng mặt trời',
            'Tư vấn bác sĩ nếu có thay đổi bất thường'
        ],
        'urgency': 'Không cấp thiết'
    },
    'scc': {
        'description': 'Ung thư biểu mô tế bào vảy là loại ung thư da phổ biến thứ hai, phát triển từ tế bào vảy ở lớp ngoài cùng của da.',
        'actions': [
            'Khám bác sĩ da liễu để chẩn đoán và điều trị',
            'Thường cần phẫu thuật cắt bỏ',
            'Có thể xâm lấn nếu không điều trị sớm',
            'Tránh ánh nắng mặt trời trực tiếp'
        ],
        'urgency': 'Cần khám sớm'
    },
    'vasc': {
        'description': 'Tổn thương mạch máu da là các thay đổi liên quan đến mạch máu dưới da.',
        'actions': [
            'Khám bác sĩ da liễu để đánh giá',
            'Có thể điều trị bằng laser nếu cần',
            'Theo dõi nếu có thay đổi hoặc chảy máu',
            'Tránh va chạm mạnh vào vùng da'
        ],
        'urgency': 'Nên khám sớm'
    }
}

# Color codes for risk levels (for frontend)
RISK_COLORS = {
    'low': '#10b981',      # green
    'medium': '#f59e0b',   # yellow/orange
    'high': '#ef4444',     # red
    'very_high': '#dc2626' # dark red
}
