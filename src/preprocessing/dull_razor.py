import cv2
import numpy as np
import os

def dull_razor(image_path):
    # Đọc ảnh bằng numpy để tránh lỗi tiếng Việt trong đường dẫn
    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    if img is None:
        print("Vẫn không đọc được ảnh, kiểm tra lại tên file!")
        return None
    # 1. Đọc ảnh và chuyển sang màu xám
    # img = cv2.imread(image_path)
    gray_scale = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 2. Black hat transformation: Làm nổi bật các sợi lông (thường tối hơn da)
    # Cấu trúc hình học (kernel) hình chữ nhật để nhận diện sợi lông dài
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    blackhat = cv2.morphologyEx(gray_scale, cv2.MORPH_BLACKHAT, kernel)

    # 3. Tạo mặt nạ (mask) cho các sợi lông bằng ngưỡng (threshold)
    # Các sợi lông sau Blackhat sẽ có màu trắng trên nền đen
    _, mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)

    # 4. Thay thế các điểm ảnh bị lông che phủ bằng kỹ thuật Inpainting
    # Thuật toán sẽ bù đắp vùng bị mất dựa trên các pixel xung quanh
    result = cv2.inpaint(img, mask, 1, cv2.INPAINT_TELEA)

    return result

# Cách sử dụng:
if __name__ == "__main__":
    # Sử dụng raw string (r) để tránh lỗi ký tự gạch chéo
    path = r"/home/khangjv/WorkSpace/MedAI_Dermatology/data/raw/images/ISIC_0024306.jpg"
    
    if not os.path.exists(path):
        print("CẢNH BÁO: Đường dẫn file không tồn tại. Hãy kiểm tra lại tên file ISIC_0024306.jpg")
    else:
        cleaned_img = dull_razor(path)
        
        if cleaned_img is not None:
            cv2.imshow("Original", cv2.imread(path)) # Nếu dòng này lỗi, dùng imdecode như trên
            cv2.imshow("Cleaned", cleaned_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    # path = r"D:\AI Da Liễu\Dermatology-Model-Agent\data\raw\images\ISIC_0024306.jpg"
    # cleaned_img = dull_razor(path)
    
    # cv2.imshow("Original", cv2.imread(path))
    # cv2.imshow("Cleaned", cleaned_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()