"""
Dịch vụ dự đoán AI Model (Phiên bản PyTorch)
Xử lý việc tải mô hình và thực hiện phán đoán
"""
import gc
import threading
import logging
from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models, transforms

from ..config import settings
from ..utils.constants import (
    CLASS_NAMES,
    CRITICAL_DISEASE_THRESHOLDS,
    DISEASE_NAMES_VI,
)

logger = logging.getLogger(__name__)


class ModelInference:
    """Lớp Singleton thread-safe cho việc dự đoán mô hình (PyTorch)"""

    _instance: Optional["ModelInference"] = None
    _lock = threading.Lock()          # Bảo vệ quá trình khởi tạo Singleton
    _model = None
    _device = None
    _normalize: Optional[transforms.Normalize] = None   # Cache transform

    # ------------------------------------------------------------------ #
    # Singleton                                                            #
    # ------------------------------------------------------------------ #
    def __new__(cls) -> "ModelInference":
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # __init__ có thể bị gọi nhiều lần trong Python (mỗi lần ModelInference())
        # → chỉ load model khi chưa có
        if self._model is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.load_model()

    # ------------------------------------------------------------------ #
    # Load model                                                           #
    # ------------------------------------------------------------------ #
    def load_model(self) -> None:
        """Tải mô hình EfficientNet-B4 đã được huấn luyện (.pth)"""
        try:
            torch.set_num_threads(settings.TORCH_THREADS)

            logger.info(f"Loading PyTorch model from {settings.MODEL_PATH}")
            logger.info(f"Device: {self._device} | Threads: {settings.TORCH_THREADS}")

            # Xây dựng kiến trúc mô hình
            self._model = models.efficientnet_b4(weights=None)
            num_ftrs = self._model.classifier[1].in_features
            self._model.classifier[1] = torch.nn.Linear(num_ftrs, len(CLASS_NAMES))

            # Tải checkpoint
            # weights_only=False vì checkpoint có thể chứa numpy object (PyTorch 2.6+)
            checkpoint = torch.load(
                str(settings.MODEL_PATH),
                map_location=self._device,
                weights_only=False,
            )

            if isinstance(checkpoint, dict) and "model_state" in checkpoint:
                state_dict = checkpoint["model_state"]
                val_acc = checkpoint.get("val_acc")
                if val_acc is not None:
                    logger.info(f"Loaded checkpoint – Val Acc: {val_acc:.4f}")
            else:
                state_dict = checkpoint
                logger.info("Loaded direct state dict")

            self._model.load_state_dict(state_dict)
            del state_dict, checkpoint
            gc.collect()

            self._model.to(self._device)

            # FP16 chỉ khi có GPU (CPU không được hỗ trợ tốt với half precision)
            if self._device.type == "cuda":
                logger.info("GPU detected: converting model to Half Precision (FP16)")
                self._model = self._model.half()
            else:
                logger.info("CPU mode: keeping Float32")

            self._model.eval()

            # Cache transform một lần duy nhất — tránh tạo lại mỗi request
            self._normalize = transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            )

            logger.info("PyTorch model loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {e}")
            # Không raise ở đây để FastAPI vẫn có thể khởi động;
            # lỗi sẽ được xử lý khi gọi predict() hoặc kiểm tra /health

    # ------------------------------------------------------------------ #
    # Predict                                                              #
    # ------------------------------------------------------------------ #
    def predict(
        self,
        image_array: np.ndarray,
    ) -> Tuple[str, float, Dict[str, float], Optional[Dict]]:
        """
        Chạy dự đoán trên ảnh đã tiền xử lý.

        Args:
            image_array: numpy array shape (1, H, W, 3), giá trị pixel 0–255

        Returns:
            Tuple gồm:
              - predicted_class (str)
              - confidence (float)
              - all_predictions (Dict[str, float], sắp xếp giảm dần)
              - critical_warning (Optional[Dict])
        """
        if self._model is None:
            self.load_model()
            if self._model is None:
                raise RuntimeError("Model chưa được load")

        try:
            # 1. Chuẩn bị tensor đầu vào
            # (1, H, W, 3) → (H, W, 3) → tensor (C, H, W) scaled [0,1]
            img_tensor = (
                torch.from_numpy(image_array[0])
                .permute(2, 0, 1)
                .float()
                .div(255.0)
            )

            # Chuẩn hóa ImageNet (dùng transform đã cache)
            img_tensor = self._normalize(img_tensor)

            # Thêm chiều batch → (1, C, H, W)
            input_tensor = img_tensor.unsqueeze(0).to(self._device)

            # Đồng bộ dtype với model (FP16 nếu GPU)
            if next(self._model.parameters()).dtype == torch.float16:
                input_tensor = input_tensor.half()

            # 2. Suy luận
            with torch.no_grad():
                outputs = self._model(input_tensor)
                probabilities = F.softmax(outputs, dim=1)[0]

            # 3. Xử lý kết quả
            probs_np: np.ndarray = probabilities.cpu().numpy()
            predicted_idx = int(np.argmax(probs_np))
            predicted_class = CLASS_NAMES[predicted_idx]
            confidence = float(probs_np[predicted_idx])

            # Dict xác suất đầy đủ, sắp xếp giảm dần
            all_predictions: Dict[str, float] = dict(
                sorted(
                    {CLASS_NAMES[i]: float(probs_np[i]) for i in range(len(CLASS_NAMES))}.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            )

            # 4. Kiểm tra ngưỡng bệnh nguy hiểm
            critical_warning: Optional[Dict] = None
            highest_crit_prob = 0.0
            highest_crit_class = None

            for crit_class, threshold in CRITICAL_DISEASE_THRESHOLDS.items():
                prob = all_predictions.get(crit_class, 0.0)
                if prob >= threshold and prob > highest_crit_prob:
                    highest_crit_prob = prob
                    highest_crit_class = crit_class

            if highest_crit_class and highest_crit_class != predicted_class:
                critical_warning = {
                    "class": highest_crit_class,
                    "confidence": highest_crit_prob,
                    "name_vi": DISEASE_NAMES_VI.get(highest_crit_class, highest_crit_class),
                }
                logger.warning(
                    f"CRITICAL WARNING: {highest_crit_class} at "
                    f"{highest_crit_prob:.2f} "
                    f"(threshold={CRITICAL_DISEASE_THRESHOLDS[highest_crit_class]})"
                )

            logger.info(f"Prediction: {predicted_class} (confidence={confidence:.3f})")

            # Dọn cache GPU nếu cần (CPU thì bỏ qua, gc ít hiệu quả ở đây)
            if self._device.type == "cuda":
                torch.cuda.empty_cache()

            return predicted_class, confidence, all_predictions, critical_warning

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise RuntimeError(f"Lỗi khi chạy AI prediction: {e}") from e

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #
    def is_loaded(self) -> bool:
        """Kiểm tra model đã tải thành công chưa."""
        return self._model is not None


# Tạo instance toàn cục (Singleton — load model ngay khi import)
model_service = ModelInference()
