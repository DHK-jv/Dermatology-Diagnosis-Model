"""
GradCAM Service for EfficientNet-B4
Generates heatmap explaining which regions the model focused on
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
    GradCAM implementation for EfficientNet-B4 (torchvision).
    Target layer: model.features[-1] (last conv block before classifier)
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self):
        """Register forward and backward hooks on the target layer"""

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
        """Remove all registered hooks"""
        for hook in self._hooks:
            hook.remove()
        self._hooks = []

    def generate(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """
        Generate GradCAM heatmap.

        Args:
            input_tensor: Normalized input tensor (1, C, H, W)
            class_idx: Class index to explain. If None, uses argmax (predicted class).

        Returns:
            heatmap: numpy array (H, W) in range [0, 1]
        """
        # Enable gradients for GradCAM
        self.model.eval()
        input_tensor.requires_grad_(True)

        # Forward pass
        output = self.model(input_tensor)

        # Use predicted class if not specified
        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        # Zero existing gradients
        self.model.zero_grad()

        # Backward pass for target class
        one_hot = torch.zeros_like(output)
        one_hot[0][class_idx] = 1
        output.backward(gradient=one_hot)

        # Pool gradients across spatial dimensions (Global Average Pooling)
        # gradients: (1, C, H, W) → weights: (C,)
        weights = self.gradients.mean(dim=[2, 3])[0]

        # Weighted sum of activations
        # activations: (1, C, H, W)
        cam = (weights[:, None, None] * self.activations[0]).sum(dim=0)

        # ReLU: keep only positive contributions
        cam = F.relu(cam)

        # Normalize to [0, 1]
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
    Full GradCAM pipeline: generate heatmap and overlay on original image.

    Args:
        model: Loaded EfficientNet-B4 model
        image_array: Original preprocessed image (1, H, W, 3), values 0-255
        device: torch device (cuda/cpu)
        class_idx: Target class index (None = use predicted class)
        alpha: Heatmap blend factor (0=only image, 1=only heatmap)

    Returns:
        base64 encoded JPEG string of the overlay image
    """
    from torchvision import transforms

    # 1. Prepare input tensor (same as inference.py)
    img = image_array[0]  # (H, W, 3)
    H, W = img.shape[:2]

    img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    img_tensor = normalize(img_tensor)
    input_tensor = img_tensor.unsqueeze(0).to(device)

    # 2. Get target layer: last block of EfficientNet-B4 features
    # model.features[-1] is the last MBConv block (output: 1792 channels)
    target_layer = model.features[-1]

    # 3. Run GradCAM
    gradcam = GradCAM(model, target_layer)
    try:
        cam = gradcam.generate(input_tensor, class_idx=class_idx)
    finally:
        gradcam.remove_hooks()

    # 4. Resize cam to match original image size
    cam_resized = cv2.resize(cam, (W, H))

    # 5. Apply colormap (JET: blue=low, red=high attention)
    heatmap = cv2.applyColorMap(
        np.uint8(255 * cam_resized),
        cv2.COLORMAP_JET
    )
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # 6. Overlay heatmap on original image
    original_img = img.astype(np.uint8)
    overlay = (alpha * heatmap + (1 - alpha) * original_img).astype(np.uint8)

    # 7. Add colorbar legend on the right side
    overlay_with_legend = _add_colorbar(overlay)

    # 8. Encode to base64 JPEG
    overlay_bgr = cv2.cvtColor(overlay_with_legend, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buffer).decode('utf-8')


def _add_colorbar(image: np.ndarray, bar_width: int = 20) -> np.ndarray:
    """
    Add a vertical colorbar (blue→red) to the right of the image.

    Args:
        image: RGB image (H, W, 3)
        bar_width: Width of the colorbar in pixels

    Returns:
        Image with colorbar appended (H, W + bar_width, 3)
    """
    H = image.shape[0]

    # Create gradient from 0 (blue) to 255 (red)
    gradient = np.linspace(255, 0, H, dtype=np.uint8).reshape(H, 1)
    gradient = np.tile(gradient, (1, bar_width))
    colorbar = cv2.applyColorMap(gradient, cv2.COLORMAP_JET)
    colorbar = cv2.cvtColor(colorbar, cv2.COLOR_BGR2RGB)

    # Add 2px white border between image and colorbar
    border = np.full((H, 2, 3), 255, dtype=np.uint8)

    return np.concatenate([image, border, colorbar], axis=1)
