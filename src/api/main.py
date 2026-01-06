from fastapi import FastAPI, File, UploadFile
from src.api.ollama_client import OllamaMedicalAdvisor
import uvicorn

app = FastAPI()
advisor = OllamaMedicalAdvisor()

@app.get("/")
def read_root():
    return {"message": "Welcome to MedAI Dermatology API"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), age: int = 0, gender: str = "Unknown"):
    # 1. Lưu ảnh hoặc chuyển ảnh sang module tiền xử lý (bạn của Khang làm)
    # 2. Gọi mô hình EfficientNet-B3 để lấy kết quả (bạn của Khang làm)
    
    # Giả lập kết quả để test luồng với Ollama
    disease_name = "Melanocytic Nevus" # Nốt ruồi lành tính [cite: 41, 184]
    confidence = 94.0 # [cite: 258]
    
    # 3. Gọi Ollama để lấy lời khuyên
    advice = advisor.get_medical_advice(
        disease_name, 
        confidence, 
        {"age": age, "gender": gender, "symptoms": "Nốt ruồi sẫm màu"}
    )
    
    return {
        "disease": disease_name,
        "confidence": f"{confidence}%",
        "medical_advice": advice
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)