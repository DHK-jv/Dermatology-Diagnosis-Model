"""
Dịch vụ dự đoán AI Model (Phiên bản PyTorch)
Xử lý việc tải mô hình và thực hiện phán đoán
"""
import os
import torch
import torch.nn.functional as F
from torchvision import transforms, models
import numpy as np
from typing import Dict, Tuple, Optional
import logging

from ..config import settings
from ..utils.constants import CLASS_NAMES

logger = logging.getLogger(__name__)


class ModelInference:
    """Lớp Singleton cho việc dự đoán mô hình (PyTorch)"""
    
    _instance = None
    _model = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Khởi tạo và tải mô hình"""
        if self._model is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.load_model()
    
    def load_model(self):
        """Tải mô hình EfficientNet đã được huấn luyện (.pth) với tối ưu bộ nhớ"""
        import gc
        try:
            # Giới hạn số luồng xử lý của PyTorch để tiết kiệm RAM trên Render
            torch.set_num_threads(settings.TORCH_THREADS)
            
            logger.info(f"Loading PyTorch model from {settings.MODEL_PATH}")
            logger.info(f"Device: {self._device} | Threads: {settings.TORCH_THREADS}")
            
            # Tạo cấu trúc mô hình sử dụng torchvision
            # Checkpoint trước đó được huấn luyện bằng torchvision.models.efficientnet_b4
            self._model = models.efficientnet_b4(weights=None)
            
            # Sửa đổi phần đầu phân loại (classifier head) để khớp với 24 lớp của chúng ta
            num_ftrs = self._model.classifier[1].in_features
            self._model.classifier[1] = torch.nn.Linear(num_ftrs, len(CLASS_NAMES))
            
            # Tải checkpoint (có cấu trúc lồng ghép)
            # Cần weights_only=False cho PyTorch 2.6+ khi checkpoint chứa object của numpy
            checkpoint = torch.load(
                str(settings.MODEL_PATH), 
                map_location=self._device,
                weights_only=False
            )
            
            # Trích xuất biến trạng thái 'state_dict' từ checkpoint
            if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
                state_dict = checkpoint['model_state']
                val_acc = checkpoint.get('val_acc', None)
                if val_acc is not None:
                    logger.info(f"Loaded checkpoint with Val Acc: {val_acc:.4f}")
            else:
                # Dự phòng cho direct state dict (chỉ có model weights cũ)
                state_dict = checkpoint
                logger.info("Đã tải direct state dict")
            
            # Tương thích state dict vào mô hình
            self._model.load_state_dict(state_dict)
            
            # Dọn dẹp bộ nhớ ngay lập tức
            del state_dict
            del checkpoint
            gc.collect()
            
            # Đặt mô hình về chế độ đánh giá (chế độ không phải Huấn luyện)
            self._model.to(self._device)
            self._model.eval()

            # Tối ưu hóa cho môi trường cực thấp RAM (Render 512MB)
            if os.environ.get("RENDER") == "true" or settings.PREPROCESSING_MODE == "opencv":
                logger.info("Chế độ bộ nhớ thấp: Chuyển mô hình sang Half Precision (FP16)")
                self._model = self._model.half()
            
            logger.info(f"Tải mô hình PyTorch thành công. Memory optimized.")
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {str(e)}")
            # Đừng ném lỗi Exception ở đây, hãy để nó ném lỗi lúc đang chạy dự đoán (predict)
            # hoặc lúc /health status, để server FastAPI vẫn có thể khởi động lên được
    
    def predict(self, image_array: np.ndarray) -> Tuple[str, float, Dict[str, float], Optional[Dict]]:
        """
        Chạy dự đoán trên ảnh đã tiền xử lý
        
        Args:
            image_array: Mảng ảnh numpy đã preprocess (1, 380, 380, 3) - Giá trị 0-255 float/uint8
            
        Returns:
            Tuple (Lớp bệnh dự đoán được, độ tin cậy, từ điển xác suất của mọi lớp, cảnh báo bệnh nguy hiểm (nếu có))
        """
        if self._model is None:
            self.load_model()
            if self._model is None:
                raise RuntimeError("Model chưa được load")
        
        try:
            # 1. Chuẩn bị tensor đầu vào cho AI
            # Bỏ chiều batch: (1, 380, 380, 3) -> (380, 380, 3)
            img = image_array[0]
            
            # Chuyển đổi thành Tensor (chứa 3 hệ màu theo chiều dọc: C, H, W) và scale 0-1
            # img hiện đang là float (0-255), nên ta sẽ chia cho 255.0
            img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            
            # Chuẩn hóa (sử dụng thông số của ImageNet)
            normalize = transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
            img_tensor = normalize(img_tensor)
            
            # Thêm chiều batch: (1, C, H, W)
            input_tensor = img_tensor.unsqueeze(0).to(self._device)
            
            # Nếu đang dùng nửa chính xác (FP16) cho Render
            if next(self._model.parameters()).dtype == torch.float16:
                input_tensor = input_tensor.half()
            
            # 2. Xử lý suy luận AI
            with torch.no_grad():
                outputs = self._model(input_tensor)
                probabilities = F.softmax(outputs, dim=1)[0]
            
            # 3. Xử lý kết quả trả về
            # Chuyển tensor thành dạng mảng numpy về thư viện của CPU
            probs_np = probabilities.cpu().numpy()
            
            # Lấy ra tên class được dự đoán mạnh nhất
            predicted_idx = np.argmax(probs_np)
            predicted_class = CLASS_NAMES[predicted_idx]
            confidence = float(probs_np[predicted_idx])
            
            # Tạo dictionary tổng hợp tất cả xác suất dự đoán (sắp xếp giảm dần)
            all_predictions = {
                CLASS_NAMES[i]: float(probs_np[i])
                for i in range(len(CLASS_NAMES))
            }
            all_predictions = dict(
                sorted(all_predictions.items(), key=lambda x: x[1], reverse=True)
            )
            
            # --- LOGIC ĐIỀU CHỈNH NGƯỠNG RỦI RO CẤP BÁCH ---
            from ..utils.constants import CRITICAL_DISEASE_THRESHOLDS, DISEASE_NAMES_VI
            
            highest_crit_prob = 0.0
            highest_crit_class = None
            critical_warning = None
            
            for crit_class, threshold in CRITICAL_DISEASE_THRESHOLDS.items():
                if crit_class in all_predictions and all_predictions[crit_class] >= threshold:
                    if all_predictions[crit_class] > highest_crit_prob:
                        highest_crit_prob = all_predictions[crit_class]
                        highest_crit_class = crit_class
            
            # NẾU CÓ BỆNH NGUY HIỂM và Bệnh đó không phải là top 1 hiện tại
            if highest_crit_class and highest_crit_class != predicted_class:
                critical_warning = {
                    "class": highest_crit_class,
                    "confidence": highest_crit_prob,
                    "name_vi": DISEASE_NAMES_VI.get(highest_crit_class, highest_crit_class)
                }
                logger.warning(
                    f"CRITICAL WARNING CREATED: {highest_crit_class} triggered at "
                    f"{highest_crit_prob:.2f} (Threshold: {CRITICAL_DISEASE_THRESHOLDS[highest_crit_class]})"
                )
            
            logger.info(
                f"Prediction complete: {predicted_class} "
                f"(confidence: {confidence:.3f})"
            )
            
            # Dọn dẹp cache và rác để duy trì RAM dưới 512MB
            import gc
            gc.collect()
            if self._device.type == 'cuda':
                torch.cuda.empty_cache()

            return predicted_class, confidence, all_predictions, critical_warning
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise RuntimeError(f"Lỗi khi chạy AI prediction: {str(e)}")
    
    def is_loaded(self) -> bool:
        """Kiểm tra xem model chẩn đoán AI đã tải thành công chưa"""
        return self._model is not None


# Tạo instance toàn cục
model_service = ModelInference()
