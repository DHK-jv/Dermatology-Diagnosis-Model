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

    def lesion_segmentation_and_crop(self, image, mask):
        """Crop lesion region based on mask. If no mask, return original image."""
        if image is None or image.size == 0:
            raise ValueError("Invalid image for segmentation")

        if mask is None or mask.size == 0:
            return image

        try:
            _, binary_mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) == 0:
                return image

            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            if w < 10 or h < 10:
                return image

            return image[y:y + h, x:x + w]
        except Exception:
            return image

    def resize_with_padding(self, image, size):
        """Resize image while preserving aspect ratio, using padding to reach target size."""
        h, w = image.shape[:2]
        target_w, target_h = size
        
        # Calculate scale to fit image within target size
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize image
        # Resize image using LANCZOS4 for maximum sharpness
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Create black canvas and paste resized image in center
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas

    def resize_image(self, image):
        """Resize to target size preserving aspect ratio."""
        if image is None or image.size == 0:
            raise ValueError("Invalid image for resize")
            
        # If it's already the target size, just return
        if image.shape[0] == self.target_size[1] and image.shape[1] == self.target_size[0]:
            return image
            
        return self.resize_with_padding(image, self.target_size)

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

    def process(self, image, mask=None, return_steps=False):
        """Run preprocessing pipeline on a numpy image (RGB or BGR)."""
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        steps = {}
        if return_steps:
            steps['original'] = image.copy()

        img_cropped = self.lesion_segmentation_and_crop(image, mask)
        if return_steps:
            steps['cropped'] = img_cropped.copy()

        # FIXED ORDER: Hair Removal -> Resize
        img_hair_removed = self.hair_removal(img_cropped)
        if return_steps:
            steps['hair_removed'] = img_hair_removed.copy()

        img_resized = self.resize_image(img_hair_removed)
        if return_steps:
            steps['resized'] = img_resized.copy()

        # Added Sharpening step for high-frequency detail enhancement
        img_sharpened = self.sharpen_image(img_resized)
        if return_steps:
            steps['sharpened'] = img_sharpened.copy()

        final_img = self.pixel_normalization(img_sharpened)
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

    def _get_mask(self, image, verbose=True):
        if self.yolo_segmentor is None:
            return None

        try:
            mask, confidence = self.yolo_segmentor.predict(
                image,
                return_confidence=True,
                verbose=verbose
            )

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

    def process(self, image, return_steps=False, verbose=True):
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        mask = None
        if self.mode == 'yolo':
            if self.yolo_segmentor is None:
                raise RuntimeError("YOLO not available but mode='yolo'")
            mask = self._get_mask(image, verbose=verbose)
        elif self.mode == 'auto':
            mask = self._get_mask(image, verbose=verbose)
        elif self.mode == 'opencv':
            mask = None

        return self.opencv_pipeline.process(image, mask=mask, return_steps=return_steps)

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
