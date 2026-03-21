"""
GradCAM Service — EfficientNet-B4 Dermatology v3.0
====================================================
Sinh biểu đồ nhiệt (heatmap) giải thích vùng mà AI tập trung khi chẩn đoán.

Tương thích với checkpoint: efficientnet_b4_derma_v3_0.pth
  - Backbone : EfficientNet-B4 (torchvision)
  - Classifier: nn.Sequential(Dropout(p=0.4), Linear(1792 → NUM_CLASSES))
  - NUM_CLASSES: 24 bệnh da liễu
  - IMG_SIZE   : 380 × 380 px
  - Normalize  : mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
  - Target layer (mặc định): model.features[-2]  (MBConv stage 7, 12×12)

CHANGELOG:
  v3.0-r3 — Focused heatmap + comparison view:
    [FIX #6] Soft mask gating + background cutoff → loại bỏ haze xanh/tím.
    [FIX #7] Alpha gamma + cutoff + focus component → core đỏ rõ hơn, viền vàng/xanh sắc nét.
    [NEW] Tùy chọn comparison view (ORIGINAL IMAGE / GRAD-CAM HEATMAP).
  v3.0-r2 — FIX "góc đỏ nuốt lesion":
    [ROOT CAUSE] Pipeline cũ: trim/clip SAU Gaussian → hot pixel góc vẫn
    đóng góp vào percentile → thắng normalize → lesion bị ép xuống xanh/tím.
    [FIX #1] Suppress 2px (thay vì 1px) trên raw 12×12 CAM.
             Hot pixel tại [1,11] giờ bị xóa ở nguồn.
    [FIX #2] Border trim (35px) chạy TRƯỚC outlier clip và Gaussian.
             Đảm bảo hot zone ~32px bị zero trước khi tính percentile.
    [FIX #3] _corner_guard(): so sánh mean của 4 góc vs trung tâm,
             zero-out bất kỳ góc nào có mean > 2× trung tâm.
    [FIX #4] Outlier clip 99.5% → 97% (hot zone 0.6% pixels nằm dưới ngưỡng cắt).
    [FIX #5] Default layer_offset = -2 (features[-2], MBConv stage 7).
             features[-1] là head conv 1×1 hay tạo edge artifact hơn.
  v3.0-r1:
    - Giảm border trim 40 → 20px, sigma H/2.2 → H/1.8, threshold 55% → 45%
    - load_v3_model(), softmax_probs, top_k predictions
  v2.x (gốc):
    - BUG #11: vệt đỏ góc; BUG #12: blue tint
"""

from __future__ import annotations

import base64
import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# ── V3.0 Model Constants ──────────────────────────────────────────────────────
_V3_IMG_SIZE    = 380
_V3_MEAN        = [0.485, 0.456, 0.406]
_V3_STD         = [0.229, 0.224, 0.225]
_V3_NUM_CLASSES = 24
_V3_DROPOUT     = 0.4

# Postprocess hyper-params (r3-optimized)
_BORDER_TRIM    = 30    # px sau upscale (giảm nhẹ để lấy thêm thông tin rìa)
_GAUSS_DIV      = 1.5   # sigma lớn hơn -> prior rộng hơn
_THRESH_PCT     = 30    # adaptive threshold percentile (giảm để giữ thêm vùng biên)
_CLIP_PCT       = 98.5  # outlier clip (tăng để giữ core mạnh hơn)
_CORNER_RATIO   = 2.2   # nới lỏng corner guard
_CAM_BORDER_PX  = 2     # border px suppress trên raw 12×12 CAM (r2: tăng từ 1 → 2)
_SMOOTH_KSIZE   = 35    # larger blur for smoother heatmap
_CAM_GAMMA      = 0.85  # <1: make heatmap "fatter" and more diffuse
_BG_CUTOFF_PCT  = 35.0  # GIẢM MẠNH (70->35) để heatmap không bị co thành "chấm đỏ"
_ALPHA_GAMMA    = 1.0   # lineary alpha for better visibility
_ALPHA_MAX      = 0.80  # hơi đậm hơn một chút
_ALPHA_CUTOFF   = 0.15  # GIẢM MẠNH (0.25->0.15) để giữ vùng halo quanh nốt bệnh
_MASK_DILATE    = 1     # expand lesion mask slightly
_MASK_BLUR      = 31    # soften lesion mask edges (odd)
_FOCUS_PCT      = 75.0  # GIẢM (88->75) để không quá khắt khe khi chọn thành phần chính
_FOCUS_MIN_AREA = 0.0010
_FOCUS_DILATE   = 3
_FOCUS_BLUR     = 51
_FINAL_CUTOFF   = 0.08  # GIẢM (0.18->0.08) để giữ toàn bộ vùng ảnh hưởng


# ── Model Loader ──────────────────────────────────────────────────────────────

def load_v3_model(
    checkpoint_path: str,
    num_classes: int = _V3_NUM_CLASSES,
    device: Optional[torch.device] = None,
) -> Tuple[nn.Module, dict]:
    """
    Load EfficientNet-B4 v3.0 từ file checkpoint (.pth).

    Checkpoint có thể lưu dưới dạng:
      - dict với key 'model_state'      (format v3.0 mới nhất)
      - dict với key 'model_state_dict' (format v2.x cũ)
      - raw state_dict

    Returns:
        model : model đã load weights, ở chế độ eval()
        meta  : dict metadata (epoch, val_f1, …) nếu có
    """
    from torchvision.models import efficientnet_b4

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = efficientnet_b4(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=_V3_DROPOUT, inplace=False),
        nn.Linear(in_features, num_classes),
    )

    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if isinstance(ckpt, dict):
        state = (
            ckpt.get("model_state")
            or ckpt.get("model_state_dict")
            or ckpt
        )
        meta = {k: v for k, v in ckpt.items() if k not in ("model_state", "model_state_dict")}
    else:
        state = ckpt
        meta  = {}

    model.load_state_dict(state)
    model.to(device)
    model.eval()
    logger.info("Loaded v3.0 | epoch=%s | val_f1=%s", meta.get("epoch", "?"), meta.get("val_f1", "?"))
    return model, meta


# ── GradCAM Core ─────────────────────────────────────────────────────────────

class GradCAM:
    """
    GradCAM cho EfficientNet-B4 (torchvision).

    Các target layer được khuyến nghị:
      model.features[-2]  MBConv stage 7 (160ch, 12×12) — ÍT ARTIFACT NHẤT ← mặc định
      model.features[-1]  head conv 1×1  (1792ch, 12×12) — ngữ nghĩa cao, dễ artifact
      model.features[-3]  MBConv stage 6 (112ch, 24×24)  — nhiều không gian hơn
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model         = model
        self.target_layer  = target_layer
        self.gradients:  Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self.last_pred_idx: Optional[int] = None
        self.last_used_idx: Optional[int] = None
        self._hooks: list = []
        self._register_hooks()

    def _register_hooks(self):
        def _fwd(module, inp, out):
            self.activations = out.detach()

        def _bwd(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self._hooks.append(self.target_layer.register_forward_hook(_fwd))
        self._hooks.append(self.target_layer.register_full_backward_hook(_bwd))

    def remove_hooks(self):
        for h in self._hooks:
            h.remove()
        self._hooks      = []
        self.gradients   = None
        self.activations = None

    def generate(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int] = None,
        force_class: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """
        Sinh raw CAM và softmax probs.

        Returns:
            cam          : (H_feat, W_feat) raw CAM sau ReLU, trước postprocess
            softmax_prob : (NUM_CLASSES,) xác suất dự đoán
            pred_idx     : lớp được dự đoán (argmax)
            used_idx     : lớp được dùng để backward
        """
        self.model.eval()
        device = next(self.model.parameters()).device
        dtype  = next(self.model.parameters()).dtype
        input_tensor = input_tensor.to(device=device, dtype=dtype)

        with torch.enable_grad():
            output = self.model(input_tensor)
            pred_idx = int(output.argmax(dim=1).item())

            if class_idx is None:
                used_idx = pred_idx
            elif force_class:
                used_idx = int(class_idx)
            else:
                used_idx = pred_idx
                if int(class_idx) != pred_idx:
                    logger.warning(
                        "GradCAM: target=%d != pred=%d → dùng pred.", class_idx, pred_idx
                    )

            self.last_pred_idx = pred_idx
            self.last_used_idx = used_idx

            self.model.zero_grad(set_to_none=True)
            output[:, used_idx].sum().backward()

        if self.gradients is None or self.activations is None:
            raise RuntimeError(
                "GradCAM hooks không bắt được gradient/activation. Kiểm tra target_layer."
            )

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1)).squeeze(0).detach().cpu().numpy().astype(np.float32)

        # FIX r2: suppress 2px biên trên raw CAM (12×12 @ 380px).
        # Hot pixel tại [1,11] hay xuất hiện do EfficientNet padding → xóa tại nguồn.
        b = _CAM_BORDER_PX
        if cam.shape[0] > b * 2 and cam.shape[1] > b * 2:
            cam[:b, :]  = 0; cam[-b:, :] = 0
            cam[:, :b]  = 0; cam[:, -b:] = 0

        softmax_prob = F.softmax(output, dim=1).squeeze(0).detach().cpu().numpy()
        return cam, softmax_prob, pred_idx, used_idx


# ── Internal helpers ──────────────────────────────────────────────────────────

def _corner_guard(
    cam: np.ndarray,
    corner_frac: float = 0.15,
    ratio: float = _CORNER_RATIO,
    peak_pct: float = 98.0,
) -> None:
    """
    Zero-out bất kỳ góc nào có mean > ratio × mean trung tâm.
    Sửa in-place. Mục tiêu: đảm bảo hot pixel góc sót lại sau trim
    không trở thành max sau normalize.

    corner_frac: tỷ lệ kích thước góc so với toàn ảnh (mặc định 15% × 15%)
    """
    H, W = cam.shape
    ch = max(1, int(H * corner_frac))
    cw = max(1, int(W * corner_frac))
    mh = int(H * 0.3); mw = int(W * 0.3)

    center_mean = float(cam[mh: H - mh, mw: W - mw].mean()) + 1e-8

    corners = [
        (slice(None, ch),  slice(None, cw)),   # top-left
        (slice(None, ch),  slice(W - cw, None)), # top-right
        (slice(H - ch, None), slice(None, cw)), # bot-left
        (slice(H - ch, None), slice(W - cw, None)), # bot-right
    ]
    for r, c in corners:
        corner_patch = cam[r, c]
        corner_peak = float(np.percentile(corner_patch, peak_pct))
        if corner_peak > ratio * center_mean:
            cam[r, c] = 0


def _soften_mask(mask: np.ndarray, H_out: int, W_out: int) -> Optional[np.ndarray]:
    """
    Tạo soft mask (0..1) từ mask binary để giảm nhiễu nền,
    giữ chuyển tiếp mượt ở viền tổn thương.
    """
    if mask is None:
        return None
    mask_np = mask
    if mask_np.ndim == 3:
        mask_np = mask_np[:, :, 0]
    if mask_np.shape[:2] != (H_out, W_out):
        mask_np = cv2.resize(mask_np, (W_out, H_out), interpolation=cv2.INTER_NEAREST)
    mask_bin = (mask_np > 0).astype(np.uint8)
    if mask_bin.max() == 0:
        return None

    if _MASK_DILATE > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask_bin = cv2.dilate(mask_bin, kernel, iterations=_MASK_DILATE)

    mask_f = mask_bin.astype(np.float32)
    k = _MASK_BLUR if _MASK_BLUR % 2 == 1 else _MASK_BLUR + 1
    mask_soft = cv2.GaussianBlur(mask_f, (k, k), 0)
    mask_soft /= mask_soft.max() + 1e-8
    return mask_soft


def _focus_component(cam: np.ndarray) -> np.ndarray:
    """
    Giữ component tập trung nhất (ưu tiên gần trung tâm, cường độ cao)
    để loại hotspot rời rạc ở góc.
    """
    if cam is None or cam.size == 0 or not np.any(cam > 0):
        return cam
    pos = cam[cam > 0]
    if pos.size == 0:
        return cam

    thresh = float(np.percentile(pos, _FOCUS_PCT))
    binary = (cam >= thresh).astype(np.uint8)

    num, labels = cv2.connectedComponents(binary, connectivity=8)
    if num <= 1:
        return cam

    H, W = cam.shape
    min_area = int(H * W * _FOCUS_MIN_AREA)
    cy, cx = H / 2.0, W / 2.0
    diag = (H * H + W * W) ** 0.5 + 1e-8

    best_label = None
    best_score = -1.0
    for label in range(1, num):
        ys, xs = np.where(labels == label)
        area = len(xs)
        if area < min_area:
            continue
        mean_val = float(cam[ys, xs].mean()) + 1e-8
        dist = (((xs.mean() - cx) ** 2 + (ys.mean() - cy) ** 2) ** 0.5) / diag
        score = (area * (mean_val ** 1.2)) / (1.0 + dist * 3.0)
        if score > best_score:
            best_score = score
            best_label = label

    if best_label is None:
        return cam

    mask = (labels == best_label).astype(np.uint8)
    if _FOCUS_DILATE > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.dilate(mask, kernel, iterations=_FOCUS_DILATE)
    k = _FOCUS_BLUR if _FOCUS_BLUR % 2 == 1 else _FOCUS_BLUR + 1
    mask_soft = cv2.GaussianBlur(mask.astype(np.float32), (k, k), 0)
    mask_soft /= mask_soft.max() + 1e-8

    cam = cam * mask_soft
    cam -= cam.min()
    cam /= cam.max() + 1e-8
    if _FINAL_CUTOFF > 0:
        cam[cam < _FINAL_CUTOFF] = 0
        cam /= cam.max() + 1e-8
    return cam


def _postprocess_cam(
    cam: np.ndarray,
    H_out: int,
    W_out: int,
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Upscale CAM về kích thước (H_out, W_out) và áp dụng chuỗi hậu xử lý.

    Thứ tự pipeline (r3):
      upscale → border trim → corner guard → outlier clip → gaussian prior
      → adaptive threshold → smoothing+gamma → soft mask (optional)
      → normalize → background cutoff → corner guard → border trim
    Thứ tự này đảm bảo hot pixel góc và haze nền bị loại trước khi overlay.
    """
    # 1. Upscale
    cam_up = cv2.resize(cam, (W_out, H_out), interpolation=cv2.INTER_LINEAR)

    # 2. Border trim TRƯỚC mọi bước khác (r2 key fix)
    t = _BORDER_TRIM
    cam_up[:t, :] = 0; cam_up[-t:, :] = 0
    cam_up[:, :t] = 0; cam_up[:, -t:] = 0

    # 3. Corner guard — loại hot pixel sót bên trong border
    _corner_guard(cam_up)

    # 4. Outlier clip 97th percentile (r2: giảm từ 99.5 → 97)
    if np.any(cam_up > 0):
        v_max = np.percentile(cam_up, _CLIP_PCT)
        cam_up = np.clip(cam_up, 0, max(float(v_max), 1e-8))

    # 5. Spatial Gaussian Prior (centre bias nhẹ)
    y, x  = np.ogrid[0:H_out, 0:W_out]
    cy, cx = H_out / 2, W_out / 2
    sy, sx = H_out / _GAUSS_DIV, W_out / _GAUSS_DIV
    prior  = np.exp(-((x - cx) ** 2 / (2 * sx ** 2) + (y - cy) ** 2 / (2 * sy ** 2)))
    cam_up = cam_up * prior

    # 6. Adaptive Threshold (loại bỏ nhiễu nền)
    pos = cam_up[cam_up > 0.01]
    if len(pos) > 0:
        low_val = np.percentile(pos, _THRESH_PCT)
        cam_up[cam_up < low_val] = 0

    # 7. Smoothing + Gamma (sharper core)
    k = _SMOOTH_KSIZE if _SMOOTH_KSIZE % 2 == 1 else _SMOOTH_KSIZE + 1
    cam_up = cv2.GaussianBlur(cam_up, (k, k), 0)
    cam_up = np.power(cam_up, _CAM_GAMMA)

    # 8. Soft lesion mask (nếu có) để loại nền nhiễu
    mask_soft = _soften_mask(mask, H_out, W_out) if mask is not None else None
    if mask_soft is not None:
        cam_up = cam_up * mask_soft

    # 9. Normalize [0, 1]
    cam_up -= cam_up.min()
    cam_up /= cam_up.max() + 1e-8

    # 10. Background cutoff (loại haze xanh/tím)
    if np.any(cam_up > 0):
        pos = cam_up[cam_up > 0]
        cutoff = float(np.percentile(pos, _BG_CUTOFF_PCT))
        cutoff = min(max(cutoff, 0.0), 0.95)
        if cutoff > 0:
            cam_up = np.clip((cam_up - cutoff) / (1.0 - cutoff + 1e-8), 0, 1)

    # 11. Focus component (loại hotspot rời rạc)
    cam_up = _focus_component(cam_up)

    # 12. Corner guard + border trim lại để tránh hotspot sau smooth
    _corner_guard(cam_up, corner_frac=0.12, ratio=_CORNER_RATIO)
    t = _BORDER_TRIM
    cam_up[:t, :] = 0; cam_up[-t:, :] = 0
    cam_up[:, :t] = 0; cam_up[:, -t:] = 0

    return cam_up


def _resolve_target_layer(model: nn.Module, layer_offset: int = -2) -> nn.Module:
    """
    Trả về target layer từ model.features[layer_offset].
    Default -2 (MBConv stage 7): ít artifact padding hơn features[-1].
    """
    if hasattr(model, "features") and len(model.features) > 0:
        return model.features[layer_offset]
    for module in reversed(list(model.modules())):
        if isinstance(module, nn.Conv2d):
            return module
    raise RuntimeError("Không tìm thấy layer phù hợp trong model.")


def _add_colorbar(image: np.ndarray, bar_width: int = 20) -> np.ndarray:
    H = image.shape[0]
    gradient = np.linspace(255, 0, H, dtype=np.uint8).reshape(H, 1)
    gradient = np.tile(gradient, (1, bar_width))
    colorbar = cv2.applyColorMap(gradient, cv2.COLORMAP_JET)
    colorbar = cv2.cvtColor(colorbar, cv2.COLOR_BGR2RGB)
    sep = np.full((H, 2, 3), 255, dtype=np.uint8)
    return np.concatenate([image, sep, colorbar], axis=1)


def _pad_to_height(image: np.ndarray, height: int, color: Tuple[int, int, int]) -> np.ndarray:
    if image.shape[0] == height:
        return image
    top = max(0, (height - image.shape[0]) // 2)
    bottom = max(0, height - image.shape[0] - top)
    return cv2.copyMakeBorder(
        image, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=color
    )


def _build_comparison_view(
    original: np.ndarray,
    heatmap: np.ndarray,
    labels: Tuple[str, str] = ("ORIGINAL IMAGE", "GRAD-CAM HEATMAP"),
    gap: int = 24,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
) -> np.ndarray:
    """
    Tạo ảnh so sánh 2 panel với nhãn tiêu đề.
    """
    orig = original.astype(np.uint8)
    heat = heatmap.astype(np.uint8)

    h = max(orig.shape[0], heat.shape[0])
    orig_p = _pad_to_height(orig, h, bg_color)
    heat_p = _pad_to_height(heat, h, bg_color)

    gap_col = np.full((h, gap, 3), bg_color, dtype=np.uint8)
    body = np.concatenate([orig_p, gap_col, heat_p], axis=1)

    header_h = max(36, int(h * 0.08))
    header = np.full((header_h, body.shape[1], 3), bg_color, dtype=np.uint8)
    canvas = np.concatenate([header, body], axis=0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.6, min(1.3, (header_h / 40.0) * 0.7))
    thickness = 2 if header_h >= 40 else 1
    color = (40, 40, 40)

    label_left, label_right = labels
    size_left = cv2.getTextSize(label_left, font, font_scale, thickness)[0]
    size_right = cv2.getTextSize(label_right, font, font_scale, thickness)[0]

    y = int(header_h * 0.7)
    x_left = int((orig_p.shape[1] - size_left[0]) / 2)
    x_right = int(orig_p.shape[1] + gap + (heat_p.shape[1] - size_right[0]) / 2)

    cv2.putText(canvas, label_left, (max(0, x_left), y), font, font_scale, color, thickness, cv2.LINE_AA)
    cv2.putText(canvas, label_right, (max(0, x_right), y), font, font_scale, color, thickness, cv2.LINE_AA)

    return canvas


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze_lesion_focus(
    cam: np.ndarray,
    mask: Optional[np.ndarray] = None,
    softmax_probs: Optional[np.ndarray] = None,
    class_names: Optional[List[str]] = None,
    top_k: int = 3,
) -> Dict:
    """
    Phân tích heatmap và đưa ra nhận định bằng lời về vùng tập trung của AI.

    Args:
        cam           : CAM đã postprocess (H, W), [0, 1]
        mask          : Binary mask vùng tổn thương hoặc None
        softmax_probs : (NUM_CLASSES,) xác suất từ model (v3.0)
        class_names   : Danh sách tên 24 lớp (v3.0)
        top_k         : Số lớp top-k trả về

    Returns:
        dict {focus, intensity, significance, confidence?, top_predictions?}
    """
    h, w = cam.shape

    # Intensity
    n_top   = max(1, int(h * w * 0.1))
    top_v   = np.sort(cam.flatten())[-n_top:] if np.any(cam > 0) else np.array([0.0])
    mean_top = float(np.mean(top_v))
    intensity = (
        "Rất cao (Rõ ràng)" if mean_top > 0.8
        else "Trung bình" if mean_top > 0.4
        else "Thấp (Phân tán)"
    )

    # Focus area
    focus_desc = "Không xác định"
    if mask is not None:
        mask_b = (mask > 0).astype(np.float32)
        total  = float(np.sum(cam)) + 1e-8
        ratio  = float(np.sum(cam * mask_b)) / total
        if ratio > 0.75:
            focus_desc = "Tập trung hoàn toàn vào vùng tổn thương"
        elif ratio > 0.4:
            k = np.ones((15, 15), np.uint8)
            border = cv2.dilate(mask_b, k, 1) - cv2.erode(mask_b, k, 1)
            focus_desc = (
                "AI chú trọng phân tích ranh giới / viền tổn thương"
                if float(np.sum(cam * border)) / total > 0.3
                else "Tập trung vào một phần vùng tổn thương"
            )
        else:
            focus_desc = "AI quan tâm đến cấu trúc da xung quanh tổn thương"
    else:
        ys, xs = np.where(cam > 0.5)
        if len(xs) > 0:
            dist = np.sqrt((np.mean(xs) - w / 2) ** 2 + (np.mean(ys) - h / 2) ** 2)
            focus_desc = (
                "AI tập trung vào vùng trung tâm tổn thương"  if dist < min(w,h)*0.2
                else "AI tập trung vào vùng lệch tâm của tổn thương" if dist < min(w,h)*0.4
                else "AI tập trung vào vùng ngoại vi / rìa ảnh"
            )
        else:
            focus_desc = "Tín hiệu phân tán, không có vùng tập trung rõ rệt"

    result: Dict = {
        "focus":        focus_desc,
        "intensity":    intensity,
        "significance": "Cao" if mean_top > 0.6 else "Vừa phải",
    }

    if softmax_probs is not None:
        pred_idx   = int(np.argmax(softmax_probs))
        confidence = float(softmax_probs[pred_idx])
        k          = min(top_k, len(softmax_probs))
        top_preds  = []
        for rank, idx in enumerate(np.argsort(softmax_probs)[::-1][:k]):
            entry: Dict = {"rank": rank + 1, "class_idx": int(idx),
                           "probability": float(softmax_probs[idx])}
            if class_names is not None and idx < len(class_names):
                entry["class_name"] = class_names[idx]
            top_preds.append(entry)
        result["confidence"]      = f"{confidence:.1%}"
        result["top_predictions"] = top_preds

    return result


# ── Main API ──────────────────────────────────────────────────────────────────

def generate_gradcam_overlay(
    model: nn.Module,
    img_preprocessed: np.ndarray,
    original_for_display: Optional[np.ndarray] = None,
    target_layer: Optional[nn.Module] = None,
    target_class: Optional[int] = None,
    mask: Optional[np.ndarray] = None,
    crop_box: Optional[List[int]] = None,
    class_names: Optional[List[str]] = None,
    layer_offset: int = -2,
    comparison_view: bool = False,
    include_colorbar: Optional[bool] = None,
    comparison_labels: Tuple[str, str] = ("ORIGINAL IMAGE", "GRAD-CAM HEATMAP"),
) -> Tuple[str, Dict]:
    """
    Tạo ảnh phủ Grad-CAM và trả về phân tích chẩn đoán.

    Args:
        model               : EfficientNet-B4 v3.0 (loaded bằng load_v3_model)
        img_preprocessed    : Ảnh 380×380, (H,W,3) hoặc (1,H,W,3), [0,1] hoặc [0,255]
        original_for_display: Ảnh gốc để overlay (H_orig,W_orig,3). None → dùng img_preprocessed
        target_layer        : Layer target GradCAM. None → auto-resolve theo layer_offset
        target_class        : Class index muốn giải thích. None → dự đoán
        mask                : Binary mask tổn thương hoặc None
        crop_box            : [x1,y1,x2,y2] nếu ảnh input đã crop từ ảnh gốc
        class_names         : Tên 24 lớp tương ứng output model
        layer_offset        : -2 (mặc định, MBConv stage 7, ít artifact)
                              -1 (head conv, ngữ nghĩa cao hơn nhưng dễ artifact)
                              -3 (MBConv stage 6, nhiều spatial detail hơn)
        comparison_view     : Nếu True, trả ảnh so sánh có nhãn.
        include_colorbar    : Nếu None → tự chọn (off khi comparison_view=True).
        comparison_labels   : Nhãn panel (ORIGINAL IMAGE / GRAD-CAM HEATMAP)

    Returns:
        (overlay_b64, analysis_dict)
    """
    from torchvision import transforms as T

    # 1. Chuẩn bị tensor
    img_np = img_preprocessed[0].copy() if img_preprocessed.ndim == 4 else img_preprocessed.copy()
    if img_np.max() <= 1.05:
        img_np = img_np * 255.0
    H_model, W_model = img_np.shape[:2]

    img_t      = torch.from_numpy(img_np.copy()).permute(2, 0, 1).float() / 255.0
    normalize  = T.Normalize(mean=_V3_MEAN, std=_V3_STD)
    input_t    = normalize(img_t).unsqueeze(0)

    # 2. Target layer
    if target_layer is None:
        target_layer = _resolve_target_layer(model, layer_offset)

    # 3. GradCAM
    gradcam = GradCAM(model, target_layer)
    try:
        cam_raw, softmax_probs, pred_idx, used_idx = gradcam.generate(
            input_t, class_idx=target_class, force_class=(target_class is not None)
        )
    finally:
        gradcam.remove_hooks()
    logger.info("GradCAM done | pred=%d used=%d cam=%s", pred_idx, used_idx, cam_raw.shape)

    # 4. Postprocess
    cam_model = _postprocess_cam(cam_raw, H_model, W_model, mask=mask)

    # 5. Map sang tọa độ ảnh gốc
    if original_for_display is not None:
        H_orig, W_orig = original_for_display.shape[:2]
        if crop_box is not None:
            x1, y1, x2, y2 = crop_box
            cw, ch = x2 - x1, y2 - y1
            scale  = min(H_model / ch, W_model / cw)
            nw, nh = int(cw * scale), int(ch * scale)
            oy, ox = (H_model - nh) // 2, (W_model - nw) // 2
            cam_crop    = cam_model[oy: oy + nh, ox: ox + nw]
            cam_display = np.zeros((H_orig, W_orig), dtype=np.float32)
            cam_display[y1:y2, x1:x2] = cv2.resize(cam_crop, (cw, ch))
        else:
            scale  = min(H_model / H_orig, W_model / W_orig)
            nw, nh = int(W_orig * scale), int(H_orig * scale)
            oy, ox = (H_model - nh) // 2, (W_model - nw) // 2
            cam_display = cv2.resize(cam_model[oy: oy + nh, ox: ox + nw], (W_orig, H_orig))
        display_base = original_for_display.astype(np.uint8)
    else:
        cam_display  = cam_model
        display_base = img_np.astype(np.uint8)

    # Extra guard after mapping to display coords
    _corner_guard(cam_display, corner_frac=0.12, ratio=_CORNER_RATIO)
    if _FINAL_CUTOFF > 0:
        cam_display = np.clip(
            (cam_display - _FINAL_CUTOFF) / (1.0 - _FINAL_CUTOFF + 1e-8),
            0,
            1,
        )

    # 6. Overlay
    heatmap = cv2.cvtColor(
        cv2.applyColorMap(np.uint8(255 * cam_display), cv2.COLORMAP_JET),
        cv2.COLOR_BGR2RGB,
    )
    alpha   = np.power(cam_display, _ALPHA_GAMMA)
    if _ALPHA_CUTOFF > 0:
        alpha[cam_display < _ALPHA_CUTOFF] = 0
    alpha   = alpha * _ALPHA_MAX
    alpha   = alpha[..., np.newaxis]
    overlay = (alpha * heatmap + (1.0 - alpha) * display_base).astype(np.uint8)

    # 7. Analysis
    analysis = analyze_lesion_focus(
        cam_model, mask=mask,
        softmax_probs=softmax_probs, class_names=class_names, top_k=3,
    )

    # 8. Encode
    if include_colorbar is None:
        include_colorbar = not comparison_view

    final = overlay
    if include_colorbar:
        final = _add_colorbar(final)
    if comparison_view:
        final = _build_comparison_view(display_base, final, labels=comparison_labels)

    _, buf    = cv2.imencode(".jpg", cv2.cvtColor(final, cv2.COLOR_RGB2BGR),
                             [cv2.IMWRITE_JPEG_QUALITY, 95])
    return base64.b64encode(buf).decode("utf-8"), analysis
