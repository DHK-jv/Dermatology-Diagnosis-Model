"""
Hybrid Preprocessing Pipeline (YOLO auto mask + OpenCV)
No manual mask input required.
Steps: YOLO mask -> Crop -> Hair Removal -> Resize -> Normalization
"""
import os
import numpy as np
import cv2

# Import YOLO (with fallback)
try:
    try:
        from preprocessing.yolo_segmentor import YOLOSegmentor, YOLO_AVAILABLE
    except ImportError:
        from yolo_segmentor import YOLOSegmentor, YOLO_AVAILABLE
except ImportError:
    YOLO_AVAILABLE = False
    YOLOSegmentor = None


class ImagePreprocessingPipeline:
    """
    OpenCV-based preprocessing pipeline.
    """
    def __init__(self, target_size=(380, 380)):
        self.target_size = target_size


    def resize_with_padding(self, image, size, is_mask=False):
        """Resize image while preserving aspect ratio, using padding to reach target size."""
        h, w = image.shape[:2]
        target_w, target_h = size
        
        # Calculate scale to fit image within target size
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize image
        # Using INTER_NEAREST for masks to preserve binary values
        interp = cv2.INTER_NEAREST if is_mask else cv2.INTER_LANCZOS4
        resized = cv2.resize(image, (new_w, new_h), interpolation=interp)
        
        # Pad to target size without black borders for images
        pad_left = (target_w - new_w) // 2
        pad_right = target_w - new_w - pad_left
        pad_top = (target_h - new_h) // 2
        pad_bottom = target_h - new_h - pad_top

        if is_mask:
            # Keep mask background = 0
            padded = cv2.copyMakeBorder(
                resized, pad_top, pad_bottom, pad_left, pad_right,
                borderType=cv2.BORDER_CONSTANT, value=0
            )
        else:
            # Use ImageNet mean padding to avoid strong activations at corners
            padded = cv2.copyMakeBorder(
                resized, pad_top, pad_bottom, pad_left, pad_right,
                borderType=cv2.BORDER_CONSTANT, value=[124, 116, 104]
            )

        return padded

    def resize_image(self, image, is_mask=False):
        """Resize to target size preserving aspect ratio."""
        if image is None or image.size == 0:
            raise ValueError("Invalid image for resize")
            
        # If it's already the target size, just return
        if image.shape[0] == self.target_size[1] and image.shape[1] == self.target_size[0]:
            return image
            
        return self.resize_with_padding(image, self.target_size, is_mask=is_mask)

    def hair_removal(self, image):
        """
        DullRazor-like hair removal
        Uses: cv2.morphologyEx (BlackHat) and cv2.inpaint
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image for hair removal")

        h, w = image.shape[:2]
        if h < 20 or w < 20:
            return image

        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            kernel_size = min(9, min(h, w) // 10)
            kernel_size = max(3, kernel_size)
            if kernel_size % 2 == 0:
                kernel_size += 1

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)

            _, hair_mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
            dst = cv2.inpaint(image, hair_mask, 1, cv2.INPAINT_TELEA)
            return dst
        except Exception:
            return image

    def sharpen_image(self, image, sigma=1.0, strength=0.8):
        """
        Apply Unsharp Mask sharpening filter to enhance texture details.
        """
        if image is None or image.size == 0:
            return image
            
        try:
            # Create a blurred version of the image
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            # Add back the high-frequency components
            sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
            return sharpened
        except Exception:
            return image

    def pixel_normalization(self, image):
        """Normalize pixel values to [0, 1]."""
        image_float = image.astype(np.float32)
        return image_float / 255.0

    def apply_clahe(self, image):
        """
        Apply Contrast Limited Adaptive Histogram Equalization.
        Works best on the L channel of LAB color space to normalize lighting/contrast.
        """
        if image is None or image.size == 0:
            return image
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # Merge channels and convert back to RGB
            limg = cv2.merge((cl, a, b))
            final = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
            return final
        except Exception:
            return image

    def lesion_segmentation_and_crop(self, image, mask, margin_ratio=0.1):
        """
        Crop lesion region based on mask with morphological cleaning and centering.
        Args:
            image: numpy array (H, W, 3)
            mask: numpy array (H, W)uint8
            margin_ratio: ratio of margin to add around the bounding box
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image for segmentation")
 
        if mask is None or mask.size == 0:
            return image, None
 
        try:
            # 1. Morphological cleaning to remove small noise and thin connections (e.g. to tools)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) == 0:
                return image, None
 
            # 2. Pick the contour that is most central and of significant size
            img_h, img_w = image.shape[:2]
            img_center = np.array([img_w / 2, img_h / 2])
            
            best_contour = None
            min_dist = float('inf')
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 500: # Skip very small noise
                    continue
                
                M = cv2.moments(cnt)
                if M["m00"] == 0: continue
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                dist = np.linalg.norm(np.array([cX, cY]) - img_center)
                # Weighted distance: prioritize large AND central objects
                weighted_dist = dist / (np.sqrt(area) + 1e-5)
                
                if weighted_dist < min_dist:
                    min_dist = weighted_dist
                    best_contour = cnt

            if best_contour is None:
                best_contour = max(contours, key=cv2.contourArea)

            x, y, w, h = cv2.boundingRect(best_contour)
            
            # 3. Add margin for context (AI needs some surrounding skin to see the border)
            mx = int(w * margin_ratio)
            my = int(h * margin_ratio)
            
            x1 = max(0, x - mx)
            y1 = max(0, y - my)
            x2 = min(img_w, x + w + mx)
            y2 = min(img_h, y + h + my)
            
            return image[y1:y2, x1:x2], mask[y1:y2, x1:x2]
        except Exception as e:
            print(f"Warning: lesion_segmentation_and_crop failed: {e}")
            return image, None
 
    def process(self, image, mask=None, return_steps=False, enhancement_enabled=True):
        """Run preprocessing pipeline on a numpy image (RGB or BGR)."""
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")
 
        if not enhancement_enabled:
            # Pure Resize mode: Skip all enhancements, just resize to target with padding
            img_resized = self.resize_image(image)
            if return_steps:
                return img_resized, {'original': image.copy(), 'resized': img_resized.copy(), 'preprocessing_applied': False}
            return img_resized

        steps = {}
        if return_steps:
            steps['original'] = image.copy()
            if mask is not None:
                steps['original_mask'] = mask.copy()
 
        img_cropped, mask_cropped = self.lesion_segmentation_and_crop(image, mask)
        if return_steps:
            steps['cropped'] = img_cropped.copy()
            if mask_cropped is not None:
                steps['mask_cropped'] = mask_cropped.copy()

        # FIXED ORDER: Hair Removal -> Resize
        img_hair_removed = self.hair_removal(img_cropped)
        if return_steps:
            steps['hair_removed'] = img_hair_removed.copy()
 
        img_resized = self.resize_image(img_hair_removed)
        # Also resize the mask if present to match the image dimensions
        final_mask = None
        if mask_cropped is not None:
            final_mask = self.resize_image(mask_cropped, is_mask=True)
            if return_steps:
                steps['mask_final'] = final_mask.copy()
 
        if return_steps:
            steps['resized'] = img_resized.copy()

        # Added Sharpening step for high-frequency detail enhancement
        img_sharpened = self.sharpen_image(img_resized)
        if return_steps:
            steps['sharpened'] = img_sharpened.copy()

        # NEW: CLAHE Color/Contrast Normalization for domain adaptation
        img_normalized_color = self.apply_clahe(img_sharpened)
        if return_steps:
            steps['color_normalized'] = img_normalized_color.copy()

        final_img = self.pixel_normalization(img_normalized_color)
        if return_steps:
            steps['normalized'] = final_img.copy()
            return final_img, steps

        return final_img

    def run(self, img_path, mask=None, return_steps=False):
        """Run preprocessing from image path."""
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"Could not read image at {img_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return self.process(img, mask=mask, return_steps=return_steps)


class HybridPreprocessingPipeline:
    """
    YOLO auto-mask + OpenCV pipeline (no manual masks).

    Modes:
        - 'auto': use YOLO if available, otherwise fallback without mask
        - 'yolo': force YOLO (error if not available)
        - 'opencv': skip YOLO and process without mask
    """
    def __init__(
        self,
        mode='auto',
        target_size=(380, 380),
        yolo_model_path=None,
        yolo_conf=0.5,
        device='cpu',
        min_confidence=0.15,
        min_mask_coverage=0.01,
        max_mask_coverage=0.60,
        min_bbox_area_ratio=0.02,
        max_aspect_ratio=5.0,
    ):
        self.mode = mode
        self.target_size = target_size
        self.device = device
        self.min_confidence = min_confidence
        self.min_mask_coverage = min_mask_coverage
        self.max_mask_coverage = max_mask_coverage
        self.min_bbox_area_ratio = min_bbox_area_ratio
        self.max_aspect_ratio = max_aspect_ratio

        self.opencv_pipeline = ImagePreprocessingPipeline(target_size=target_size)

        self.yolo_segmentor = None
        if mode in ['auto', 'yolo'] and YOLO_AVAILABLE and YOLOSegmentor is not None:
            try:
                self.yolo_segmentor = YOLOSegmentor(
                    model_path=yolo_model_path,
                    conf_threshold=yolo_conf,
                    device=device
                )
            except Exception:
                self.yolo_segmentor = None
                if mode == 'yolo':
                    raise RuntimeError("YOLO mode selected but YOLO not available")

    def _get_mask(self, image, verbose=False):
        if self.yolo_segmentor is None:
            return None

        try:
            mask, confidence = self.yolo_segmentor.predict(
                image,
                return_confidence=True,
                verbose=verbose
            )

            # Safety check: mask might be None if YOLO fails to detect any object
            if mask is None:
                return None

            if confidence < self.min_confidence:
                if verbose:
                    print(f"YOLO mask rejected: low confidence {confidence:.2f}")
                return None

            # Coverage check
            coverage = float((mask > 0).mean())
            if coverage < self.min_mask_coverage or coverage > self.max_mask_coverage:
                if verbose:
                    print(f"YOLO mask rejected: coverage {coverage:.3f}")
                return None

            # Bounding box sanity check (avoid thin hair-like masks)
            ys, xs = np.where(mask > 0)
            if len(xs) == 0 or len(ys) == 0:
                return None
            x1, x2 = xs.min(), xs.max()
            y1, y2 = ys.min(), ys.max()
            w = x2 - x1 + 1
            h = y2 - y1 + 1
            if w <= 0 or h <= 0:
                return None

            bbox_area = w * h
            img_area = mask.shape[0] * mask.shape[1]
            if (bbox_area / img_area) < self.min_bbox_area_ratio:
                if verbose:
                    print(f"YOLO mask rejected: bbox area ratio {bbox_area/img_area:.3f}")
                return None

            aspect_ratio = max(w / h, h / w)
            if aspect_ratio > self.max_aspect_ratio:
                if verbose:
                    print(f"YOLO mask rejected: aspect ratio {aspect_ratio:.2f}")
                return None

            return mask
        except Exception:
            return None

    def _limit_resolution(self, image, max_dim=1024):
        """Limit image resolution before expensive steps like hair removal."""
        h, w = image.shape[:2]
        if max(h, w) <= max_dim:
            return image
        
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def process(self, image, return_steps=False, verbose=False, enhancement_enabled=True):
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        if not enhancement_enabled:
            return self.opencv_pipeline.process(image, mask=None, return_steps=return_steps, enhancement_enabled=False)

        # Bug Fix: Limit resolution BEFORE YOLO mask generation to ensure mask matches image size
        image_limited = self._limit_resolution(image, 1024)

        mask = None
        if self.mode == 'yolo':
            if self.yolo_segmentor is None:
                raise RuntimeError("YOLO not available but mode='yolo'")
            mask = self._get_mask(image_limited, verbose=verbose)
        elif self.mode == 'auto':
            mask = self._get_mask(image_limited, verbose=verbose)
        elif self.mode == 'opencv':
            mask = None

        return self.opencv_pipeline.process(image_limited, mask=mask, return_steps=return_steps, enhancement_enabled=True)

    def run(self, image_path, return_steps=False, verbose=True):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return self.process(image, return_steps=return_steps, verbose=verbose)

    def batch_process(self, image_paths, output_dir=None, verbose=False):
        results = []
        for img_path in image_paths:
            try:
                processed = self.run(img_path, verbose=verbose)
                results.append(processed)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f"processed_{os.path.basename(img_path)}")
                    save_img = (processed * 255).astype(np.uint8)
                    cv2.imwrite(output_path, cv2.cvtColor(save_img, cv2.COLOR_RGB2BGR))
            except Exception:
                results.append(None)
        return results

    def get_stats(self):
        return {
            'mode': self.mode,
            'target_size': self.target_size,
            'yolo_available': self.yolo_segmentor is not None,
            'opencv_available': True,
            'device': self.device,
            'min_confidence': self.min_confidence,
            'min_mask_coverage': self.min_mask_coverage,
            'max_mask_coverage': self.max_mask_coverage,
            'min_bbox_area_ratio': self.min_bbox_area_ratio,
            'max_aspect_ratio': self.max_aspect_ratio
        }
