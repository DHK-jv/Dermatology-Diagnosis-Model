"""
Dịch vụ GradCAM cho EfficientNet-B4
Sinh ra biểu đồ nhiệt (heatmap) giải thích các vùng mà mô hình AI đã tập trung vào
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GradCAM:
    """
    Cài đặt thuật toán GradCAM cho EfficientNet-B4 (dùng torchvision).
    Lớp mục tiêu: model.features[-1] (khối conv cuối cùng trước khi phân loại)
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.last_pred_idx = None
        self.last_used_idx = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self):
        """Đăng ký các hook chuyển tiếp (forward) và truyền ngược (backward) trên lớp mục tiêu"""

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self._hooks.append(
            self.target_layer.register_forward_hook(forward_hook)
        )
        self._hooks.append(
            self.target_layer.register_full_backward_hook(backward_hook)
        )

    def remove_hooks(self):
        """Gỡ bỏ tất cả các hook đã đăng ký"""
        for hook in self._hooks:
            hook.remove()
        self._hooks = []
        self.gradients = None
        self.activations = None

    def generate(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int] = None,
        force_class: bool = False,
    ) -> np.ndarray:
        """
        Sinh biểu đồ nhiệt GradCAM.

        Args:
            input_tensor: Tensor đầu vào đã được chuẩn hóa (1, C, H, W)
            class_idx: Chỉ số lớp (class) cần giải thích. Nếu là None, sẽ dùng hàm argmax (lớp được dự đoán).

        Returns:
            heatmap: mảng numpy (H, W) nằm trong khoảng giá trị [0, 1]
        """
        # Bật tính toán gradient cho GradCAM
        self.model.eval()

        with torch.enable_grad():
            # Truyền tiến (Forward pass)
            output = self.model(input_tensor)

            pred_idx = int(output.argmax(dim=1).item())
            if class_idx is not None and int(class_idx) != pred_idx:
                logger.warning(
                    f"GradCAM: target class {class_idx} != predicted {pred_idx}. "
                    f"{'Using target class.' if force_class else 'Using predicted class.'}"
                )

            if class_idx is None:
                used_idx = pred_idx
            elif force_class:
                used_idx = int(class_idx)
            else:
                used_idx = pred_idx

            self.last_pred_idx = pred_idx
            self.last_used_idx = used_idx

            # Xóa các gradient hiện có
            self.model.zero_grad(set_to_none=True)

            # Truyền ngược (Backward pass) cho lớp mục tiêu
            try:
                score = output[:, used_idx].sum()
                score.backward()
            except Exception as e:
                logger.error(f"Error during backward pass: {str(e)}")
                raise

        # Tổng hợp gradient qua các chiều không gian (Global Average Pooling)
        # gradients: (1, C, H, W) → weights: (C,)
        if self.gradients is None or self.activations is None:
            raise RuntimeError("GradCAM hooks did not capture gradients/activations. Check target_layer.")

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)

        # Tính tổng có trọng số của các kích hoạt (activations)
        # activations: (1, C, H, W)
        cam = (weights * self.activations).sum(dim=1)  # (1, H, W)

        # ReLU: chỉ giữ lại các ảnh hưởng mang tính đóng góp tích cực
        cam = F.relu(cam).squeeze(0)

        # Chuẩn hóa giá trị về khoảng [0, 1]
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)

        return cam.detach().cpu().numpy()


def _resolve_target_layer(model) -> torch.nn.Module:
    """
    Ưu tiên lớp conv cuối cùng trong EfficientNet (features[-1]).
    Fallback: tìm Conv2d cuối cùng trong toàn bộ model.
    """
    # Đối với EfficientNet-B4, features[7] là nhóm MBConv cuối cùng (chứa 3x3 conv).
    # features[8] là layer 1x1 expansion, thường cho heatmap kém chi tiết hơn về mặt không gian.
    if hasattr(model, "features") and len(model.features) > 7:
        return model.features[7]
    elif hasattr(model, "features") and len(model.features) > 0:
        return model.features[-1]

    for module in reversed(list(model.modules())):
        if isinstance(module, nn.Conv2d):
            return module

    raise RuntimeError("Không tìm thấy Conv2d phù hợp để làm target_layer.")


def generate_gradcam_overlay(
    model,
    image_array: np.ndarray,
    device: torch.device,
    class_idx: Optional[int] = None,
    alpha: float = 0.5,
    mask: Optional[np.ndarray] = None
) -> str:
    """
    Toàn bộ luồng (pipeline) GradCAM: sinh biểu đồ nhiệt và phủ đè lên ảnh gốc.

    Args:
        model: Mô hình EfficientNet-B4 đã được tải
        image_array: Ảnh gốc đã qua tiền xử lý (1, H, W, 3), các giá trị từ 0-255
        device: Chạy trên thiết bị torch nào (cuda/cpu)
        class_idx: Chỉ số lớp (class) mục tiêu (None = sử dụng lớp được dự đoán)
        alpha: Tỷ lệ hòa trộn trộn biểu đồ nhiệt (0=chỉ hiện ảnh, 1=chỉ hiện biểu đồ nhiệt)

    Returns:
        Chuỗi dạng base64 chứa hình ảnh kết quả phủ đè
    """
    from torchvision import transforms

    # 1. Chuẩn bị tensor đầu vào (giống hệt luồng ở file inference.py)
    img = image_array[0].copy()  # (H, W, 3)
    # Đảm bảo ảnh nằm trong dải [0, 255] trước khi chia 255.0 để tạo tensor
    if img.max() <= 1.05:
        img = img * 255.0
        
    H, W = img.shape[:2]

    img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    input_tensor = normalize(img_tensor)
    input_tensor = input_tensor.unsqueeze(0).to(device)

    # Đảm bảo tensor cùng kiểu với model (FP16 / FP32)
    if next(model.parameters()).dtype == torch.float16:
        input_tensor = input_tensor.half()

    # 2. Lấy lớp mục tiêu: Conv cuối cùng (features[-1]) cho GradCAM ổn định
    target_layer = _resolve_target_layer(model)

    # 3. Chạy GradCAM
    gradcam = GradCAM(model, target_layer)
    try:
        cam = gradcam.generate(input_tensor, class_idx=class_idx, force_class=True)
    finally:
        gradcam.remove_hooks()

    # 4. Upscale lên độ phân giải gốc (giữ chi tiết, tránh làm mờ quá mức)
    cam_resized = cv2.resize(cam, (W, H), interpolation=cv2.INTER_LINEAR)

    # 5. Làm mịn mạnh để heatmap trông tự nhiên, không bị vỡ khối hoặc quá thô
    cam_resized = cv2.GaussianBlur(cam_resized, (21, 21), 0)

    # 6. Giới hạn vùng bệnh (Lesion Bounding) nếu có mask
    if mask is not None:
        if mask.shape[:2] != (H, W):
            mask_resized = cv2.resize(mask, (W, H), interpolation=cv2.INTER_NEAREST)
        else:
            mask_resized = mask
        mask_float = mask_resized.astype(float) / 255.0
        cam_resized = cam_resized * mask_float
    else:
        # Tự động tạo mask loại bỏ vùng padding (124, 116, 104) để không sinh nhiệt ngoài viền
        padded_pixel = np.array([124, 116, 104], dtype=img.dtype)
        diff = np.abs(img - padded_pixel).sum(axis=-1)
        content_mask = (diff > 5).astype(float)
        cam_resized = cam_resized * content_mask

    # 7. Loại bỏ vùng nhiệt thấp theo percentile để tránh "đỏ toàn ảnh"
    # 7. Loại bỏ vùng nhiễu nhiệt cực thấp (dùng 40th percentile để giữ nhiều ngữ cảnh hơn)
    if cam_resized.max() > 0:
        thresh = np.percentile(cam_resized, 40)
        cam_resized = np.clip(cam_resized - thresh, 0, None)
        cam_resized = cam_resized / (cam_resized.max() + 1e-8)
    else:
        cam_resized = np.zeros_like(cam_resized)

    # 8. Áp dụng bản đồ màu (JET: xanh dương=thấp, đỏ=chú ý cao)
    heatmap = cv2.applyColorMap(
        np.uint8(255 * cam_resized),
        cv2.COLORMAP_JET
    )
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # 9. Phủ biểu đồ nhiệt đè lên ảnh gốc
    original_img = img.astype(np.uint8)
    overlay = (alpha * heatmap + (1 - alpha) * original_img).astype(np.uint8)

    # 10. Thêm chú giải thanh màu (colorbar) ở cạnh phải màn hình
    overlay_with_legend = _add_colorbar(overlay)

    # 11. Mã hóa thẻ ảnh JPEG thành định dạng cơ số 64 (base64)
    overlay_bgr = cv2.cvtColor(overlay_with_legend, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 12. Dọn dẹp bộ nhớ tích cực (Rất quan trọng cho 512MB RAM)
    import gc
    del cam, cam_resized, heatmap, overlay, overlay_with_legend, original_img, input_tensor
    if device.type == 'cuda':
        torch.cuda.empty_cache()
    gc.collect()
    
    return base64.b64encode(buffer).decode('utf-8')


def _add_colorbar(image: np.ndarray, bar_width: int = 20) -> np.ndarray:
    """
    Thêm một thanh màu dọc (colorbar) (xanh→đỏ) vào phía bên phải của ảnh.

    Args:
        image: Ảnh RGB (H, W, 3)
        bar_width: Chiều rộng của thanh màu bằng pixels

    Returns:
        Hình ảnh bao gồm cả ảnh cũ + thanh màu gộp lại vào chung (H, W + bar_width, 3)
    """
    H = image.shape[0]

    # Tạo dải phân màu gradient từ 0 (xanh dương) tới 255 (đỏ)
    gradient = np.linspace(255, 0, H, dtype=np.uint8).reshape(H, 1)
    gradient = np.tile(gradient, (1, bar_width))
    colorbar = cv2.applyColorMap(gradient, cv2.COLORMAP_JET)
    colorbar = cv2.cvtColor(colorbar, cv2.COLOR_BGR2RGB)

    # Thêm viền trắng mỏng 2px giữa ảnh và thanh màu
    border = np.full((H, 2, 3), 255, dtype=np.uint8)

    return np.concatenate([image, border, colorbar], axis=1)
