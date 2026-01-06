import cv2
import numpy as np

class ImageCleaner:
    def __init__(self, target_size=(300, 300)):
        self.target_size = target_size

    def process(self, image_path):
        """
        Quy trình tiền xử lý: Đọc -> Crop -> Resize -> Normalize
        """
        # 1. Đọc ảnh từ đường dẫn
        img = cv2.imread(image_path)
        if img is None:
            return None

        # 2. Crop: Cắt ảnh ở trung tâm để loại bỏ bớt nền thừa [cite: 16, 227]
        h, w = img.shape[:2]
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        img_cropped = img[start_y:start_y+min_dim, start_x:start_x+min_dim]

        # 3. Resize: Đưa về kích thước 300x300 pixel [cite: 17, 114, 228]
        img_resized = cv2.resize(img_cropped, self.target_size)

        # 4. Normalize: Chuẩn hóa giá trị pixel về đoạn [0, 1] [cite: 19, 116, 240]
        # Giúp mô hình ổn định và hội tụ nhanh hơn [cite: 19, 242]
        img_normalized = img_resized.astype(np.float32) / 255.0

        return img_normalized

# Cách sử dụng thử nghiệm
if __name__ == "__main__":
    cleaner = ImageCleaner()
    # Thay 'path_to_image.jpg' bằng một file ảnh thực tế trong folder data/raw
    processed_img = cleaner.process('data/raw/test_image.jpg')
    if processed_img is not None:
        print(f"Kích thước ảnh sau xử lý: {processed_img.shape}")