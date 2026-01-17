from src.preprocessing.image_cleaner import ImagePreprocessingPipeline
import matplotlib.pyplot as plt

pipeline = ImagePreprocessingPipeline()

# Khang dùng 1 ID ảnh đã check 'True'
img_id = "ISIC_0024306"
img_path = f"data/raw/images/{img_id}.jpg"
mask_path = f"data/masks/lesion/{img_id}_segmentation.png"

try:
    result = pipeline.run(img_path, mask_path)
    print(f"Kích thước sau cùng: {result.shape}") # (300, 300, 3)
    print(f"Giá trị Pixel max: {result.max()}")   # Phải <= 1.0
    
    # Hiển thị ảnh để kiểm tra bằng mắt
    plt.imshow(result)
    plt.show()
except Exception as e:
    print(f"Lỗi kết nối hoặc file: {e}")