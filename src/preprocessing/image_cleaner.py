import cv2
import numpy as np

class ImagePreprocessingPipeline:
    def __init__(self, target_size=(300, 300)):
        self.target_size = target_size

    def lesion_segmentation_and_crop(self, image, mask):
        """
        Crop vùng tổn thương dựa trên mask segmentation
        """
        # Nhị phân hóa mask
        _, binary_mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

        # Tìm contour tổn thương
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Nếu không tìm thấy mask → trả ảnh gốc
        if len(contours) == 0:
            return image

        # Lấy vùng tổn thương lớn nhất
        largest_contour = max(contours, key=cv2.contourArea)

        # Bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Crop ROI
        cropped = image[y:y + h, x:x + w]

        return cropped

        # return image 

    # def resize_image(self, image):
    #     """Bước 2: đưa ảnh về kích thước 300x300"""
    #     return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)

    def resize_image(self, image):
        """ Bước 3: Thay đổi kích thước bằng OpenCV """
        # Nếu ảnh đã đúng kích thước thì trả về luôn
        if image.shape[:2] == self.target_size:
            return image
            
        # cv2.INTER_AREA là lựa chọn tốt nhất để giảm kích thước ảnh (Downsampling)
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
        # return cv2.resize(image, self.target_size)

    def hair_removal(self, image):
        """ 
        Bước 4: Thuật toán DullRazor
        Sử dụng: cv2.morphologyEx (BlackHat) và cv2.inpaint 
        """
        # 1. Chuyển sang ảnh xám
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. BlackHat để làm nổi bật sợi lông
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        
        # 3. Tạo mặt nạ sợi lông
        _, hair_mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
        
        # 4. Inpaint để bù đắp vùng da dưới sợi lông
        dst = cv2.inpaint(image, hair_mask, 1, cv2.INPAINT_TELEA)
        return dst
        # return image

    def pixel_normalization(self, image):
        """ Bước 5: Chuẩn hóa giá trị Pixel về [0, 1] """
        # 1. Chuyển kiểu dữ liệu sang float32 để tính toán chính xác
        image_float = image.astype(np.float32)
        
        # 2. Chia cho 255 để đưa giá trị về khoảng [0, 1]
        normalized_image = image_float / 255.0
        
        return normalized_image
        # return image.astype(np.float32) / 255.0

    def run(self, img_path, mask_path):
        """ Thực thi toàn bộ quy trình """
        img = cv2.imread(img_path) 
        mask = cv2.imread(mask_path, 0) # Load mask ở dạng grayscale

        # Thực hiện các bước theo thứ tự
        img = self.lesion_segmentation_and_crop(img, mask) # Lesion Segmentation & Crop
        img = self.resize_image(img)                       # Resize to 300x300
        img = self.hair_removal(img)                       # Hair Removal
        final_img = self.pixel_normalization(img)          # Pixel Value Normalization

        return final_img


if __name__ == "__main__":
    # 1. Khởi tạo Pipeline
    pipeline = ImagePreprocessingPipeline(target_size=(300, 300))

    # 2. Đường dẫn file (Hãy thay đổi đường dẫn này đúng với file trong máy bạn)
    img_path = r"D:\AI_Da_Lieu\Dermatology-Model-Agent\data\raw\images\ISIC_0024307.jpg"
    mask_path = r"D:\AI_Da_Lieu\Dermatology-Model-Agent\data\masks\lesion\ISIC_0024307_segmentation.png"

    try:
        result = pipeline.run(img_path, mask_path)

        # Hiển thị ảnh
        cv2.imshow("Ket qua xu ly", (result * 255).astype(np.uint8))
        
        print("Da xu ly xong! Nhan phim bat ky de thoat.") # Không dùng dấu
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}") # Để hiện lỗi bằng tiếng Anh cho dễ đọc


# import cv2
# import numpy as np

# class ImageCleaner:
#     def __init__(self, target_size=(300, 300)):
#         self.target_size = target_size

#     def process(self, image_path):
#         """
#         Quy trình tiền xử lý: Đọc -> Crop -> Resize -> Normalize
#         """
#         # 1. Đọc ảnh từ đường dẫn
#         img = cv2.imread(image_path)
#         if img is None:
#             return None

#         # 2. Crop: Cắt ảnh ở trung tâm để loại bỏ bớt nền thừa [cite: 16, 227]
#         h, w = img.shape[:2]
#         min_dim = min(h, w)
#         start_x = (w - min_dim) // 2
#         start_y = (h - min_dim) // 2
#         img_cropped = img[start_y:start_y+min_dim, start_x:start_x+min_dim]

#         # 3. Resize: Đưa về kích thước 300x300 pixel [cite: 17, 114, 228]
#         img_resized = cv2.resize(img_cropped, self.target_size)

#         # 4. Normalize: Chuẩn hóa giá trị pixel về đoạn [0, 1] [cite: 19, 116, 240]
#         # Giúp mô hình ổn định và hội tụ nhanh hơn [cite: 19, 242]
#         img_normalized = img_resized.astype(np.float32) / 255.0

#         return img_normalized

# # Cách sử dụng thử nghiệm
# if __name__ == "__main__":
#     cleaner = ImageCleaner()
#     # Thay 'path_to_image.jpg' bằng một file ảnh thực tế trong folder data/raw
#     processed_img = cleaner.process('data/raw/test_image.jpg')
#     if processed_img is not None:
#         print(f"Kích thước ảnh sau xử lý: {processed_img.shape}")