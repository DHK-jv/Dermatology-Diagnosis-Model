"""
Dịch vụ GradCAM cho EfficientNet-B4
Sinh ra biểu đồ nhiệt (heatmap) giải thích các vùng mà mô hình AI đã tập trung vào
"""
import torch
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

    def generate(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> np.ndarray:
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
        input_tensor.requires_grad_(True)

        # Truyền tiến (Forward pass)
        output = self.model(input_tensor)

        # Sử dụng lớp được dự đoán nếu người dùng không tự chỉ định
        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        # Xóa các gradient hiện có
        self.model.zero_grad()

        # Truyền ngược (Backward pass) cho lớp mục tiêu
        one_hot = torch.zeros_like(output)
        one_hot[0][class_idx] = 1
        output.backward(gradient=one_hot)

        # Tổng hợp gradient qua các chiều không gian (Global Average Pooling)
        # gradients: (1, C, H, W) → weights: (C,)
        weights = self.gradients.mean(dim=[2, 3])[0]

        # Tính tổng có trọng số của các kích hoạt (activations)
        # activations: (1, C, H, W)
        cam = (weights[:, None, None] * self.activations[0]).sum(dim=0)

        # ReLU: chỉ giữ lại các ảnh hưởng mang tính đóng góp tích cực
        cam = F.relu(cam)

        # Chuẩn hóa giá trị về khoảng [0, 1]
        cam = cam.cpu().numpy()
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam


def generate_gradcam_overlay(
    model,
    image_array: np.ndarray,
    device: torch.device,
    class_idx: Optional[int] = None,
    alpha: float = 0.5
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
    img = image_array[0]  # (H, W, 3)
    H, W = img.shape[:2]

    img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    img_tensor = normalize(img_tensor)
    input_tensor = img_tensor.unsqueeze(0).to(device)

    # 2. Lấy lớp mục tiêu: khối cuối cùng của các đặc trưng (features) bên trong EfficientNet-B4
    # model.features[-1] là khối MBConv cuối cùng (đầu ra có: 1792 kênh)
    target_layer = model.features[-1]

    # 3. Chạy GradCAM
    gradcam = GradCAM(model, target_layer)
    try:
        cam = gradcam.generate(input_tensor, class_idx=class_idx)
    finally:
        gradcam.remove_hooks()

    # 4. Đổi kích thước (resize) cam để vừa khít với kích thước ảnh gốc
    cam_resized = cv2.resize(cam, (W, H))

    # 5. Áp dụng bản đồ màu (JET: xanh dương=thấp, đỏ=chú ý cao)
    heatmap = cv2.applyColorMap(
        np.uint8(255 * cam_resized),
        cv2.COLORMAP_JET
    )
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # 6. Phủ biểu đồ nhiệt đè lên ảnh gốc
    original_img = img.astype(np.uint8)
    overlay = (alpha * heatmap + (1 - alpha) * original_img).astype(np.uint8)

    # 7. Thêm chú giải thanh màu (colorbar) ở cạnh phải màn hình
    overlay_with_legend = _add_colorbar(overlay)

    # 8. Mã hóa thẻ ảnh JPEG thành định dạng cơ số 64 (base64)
    overlay_bgr = cv2.cvtColor(overlay_with_legend, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 9. Dọn dẹp bộ nhớ tích cực (Rất quan trọng cho 512MB RAM)
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
