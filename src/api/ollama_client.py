import requests
import json

class OllamaMedicalAdvisor:
    def __init__(self, model_name="llama3"):
        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = model_name
        
        # Giải pháp 1: Vô hiệu hóa proxy cho localhost ngay trong code
        os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

    def get_medical_advice(self, disease_name, confidence, clinical_data):
        """
        Gửi kết quả từ mô hình AI sang Ollama để lấy lời khuyên.
        """
        # Tạo prompt thông minh dựa trên dữ liệu thực tế
        prompt = f"""
        Hệ thống AI vừa chẩn đoán bệnh nhân có khả năng bị {disease_name} 
        với độ tin cậy {confidence}%.
        Thông tin lâm sàng:
        - Tuổi: {clinical_data.get('age')}
        - Giới tính: {clinical_data.get('gender')}
        - Triệu chứng: {clinical_data.get('symptoms')}
        
        Hãy đưa ra 3 lời khuyên y tế ngắn gọn và một cảnh báo rằng 
        đây chỉ là kết quả tham khảo từ AI, không thay thế bác sĩ.
        """

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            # Giải pháp 2: Yêu cầu requests không dùng proxy
            session = requests.Session()
            session.trust_env = False 
            
            response = session.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Không thể lấy lời khuyên.")
        except Exception as e:
            return f"Lỗi kết nối Ollama: {str(e)}"

# Thử nghiệm nhanh
if __name__ == "__main__":
    advisor = OllamaMedicalAdvisor()
    # Giả sử AI dự đoán là Ung thư hắc tố (MEL) [cite: 40]
    sample_advice = advisor.get_medical_advice(
        "Melanoma (Ung thư hắc tố)", 
        85.5, 
        {"age": 45, "gender": "Nam", "symptoms": "Ngứa và chảy máu"}
    )
    print(sample_advice)