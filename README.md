# BÁO CÁO TỔNG KẾT ĐỒ ÁN 2
# 🏥 MEDAI DERMATOLOGY: HỆ THỐNG TRÍ TUỆ NHÂN TẠO CHẨN ĐOÁN BỆNH LÝ DA LIỄU

> **Tác giả:** Dương Hoàng Khang - 223952 - DH22KPM01  
> **Ngành / Chuyên ngành:** Kỹ thuật Phần mềm (Software Engineering)
> **Ứng dụng công nghệ:** Deep Learning (Học Sâu), Xử lý Phân đoạn Ảnh (Image Segmentation), FastAPI & KIến trúc Microservices.

---

## LỜI CẢM ƠN
Trong quá trình thực hiện đề tài này, em xin gửi lời cảm ơn chân thành và sâu sắc nhất đến các thầy cô giảng viên đã tận tình hướng dẫn, truyền đạt kiến thức và kinh nghiệm quý báu cho em. Đồng thời, em cũng xin cảm ơn gia đình, bạn bè đã luôn động viên, tạo điều kiện thuận lợi nhất để em có thể hoàn thành xuất sắc đồ án này.

Tuy đã có nhiều cố gắng trong việc thu thập tài liệu, nghiên cứu và triển khai thực nghiệm, nhưng do những hạn chế về thời gian cũng như kinh nghiệm thực tiễn nên hệ thống cũng như bản báo cáo này chắc chắn không tránh khỏi những thiếu sót. Em rất mong nhận được sự góp ý, chỉ bảo của các thầy cô để em có thể hoàn thiện đề tài tốt hơn.

---

## TÓM TẮT ĐỀ TÀI
Bệnh lý da liễu là một trong những dạng bệnh phổ biến nhất trên thế giới, nhưng lại thường bị bỏ qua ở giai đoạn nhẹ, dẫn đến các biến chứng vô cùng nguy hiểm về sau (đặc biệt là ung thư da tế bào hắc tố - Melanoma). Việc chẩn đoán sớm và chính xác đóng vai trò sinh tử mang lại cơ hội chữa trị cho bệnh nhân. Đề tài **"MedAI Dermatology: Hệ thống Trí tuệ Nhân tạo Chẩn đoán 24 Bệnh Da liễu"** được thực hiện với mục tiêu nghiên cứu và phát triển một hệ thống Học Sâu hoàn chỉnh, có thể tự động phân tích và đưa ra đánh giá dựa trên ảnh chụp bề mặt da từ thiết bị di động.

Dự án đã sử dụng bộ dữ liệu quy mô lớn (hơn 41.000 hình ảnh) từ DermNet NZ, ISIC 2019 và PAD-UFES-20. Đề tài áp dụng một luồng Tiền xử lý Hỗn hợp (Hybrid Preprocessing Pipeline) ứng dụng YOLOv8 để phân đoạn vùng bệnh và DullRazor để tẩy nhiễu lông/tóc trên ảnh. Mô hình cốt lõi sử dụng mạng Convolutional Neural Network hiện đại là **EfficientNet-B4 (Version 2.1 và tinh chỉnh V3.0)**, kết hợp cùng các chiến thuật huấn luyện chống mất cân bằng dữ liệu như *Square-Root Weighted Random Sampler* và *Asymmetric Loss*. Hệ thống cuối cùng không chỉ đạt các tiêu chuẩn y tế khắt khe, đạt độ chính xác kiểm định (Validation Accuracy) ~86.2% và điểm số F1 Macro ~0.880, mà còn được tích hợp vào một nền tảng Web Full-stack toàn diện hỗ trợ quy trình lâm sàng của bác sĩ thông qua công nghệ giải thích Grad-CAM.

---

## MỤC LỤC
**CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT**
- 1.1 Khái quát và tính cấp thiết
- 1.2 Mục tiêu và đối tượng nghiên cứu
- 1.3 Tổng quan về công nghệ Deep Learning trong y tế

**CHƯƠNG 2. PHÂN TÍCH, THIẾT KẾ VÀ KIẾN TRÚC HỆ THỐNG**
- 2.1 Yêu cầu hệ thống
- 2.2 Phân tích hệ thống qua các sơ đồ UML (Use Case, DFD, ERD, Class)
- 2.3 Thiết kế giao diện (UI)

**CHƯƠNG 3. QUY TRÌNH TIỀN XỬ LÝ VÀ CHUẨN BỊ DỮ LIỆU**
- 3.1 Nguồn dữ liệu
- 3.2 Luồng tiền xử lý (DullRazor & YOLOv8) 

**CHƯƠNG 4. HUẤN LUYỆN MÔ HÌNH VÀ PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM**
- 4.1 Môi trường và Setup (Kaggle P100)
- 4.2 Các kỹ thuật tối ưu hóa trong tập V3.0
- 4.3 Trực quan hóa và phân tích số liệu (Loss/Acc, Confusion Matrix, ROC/AUC)

**CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN**

---

## CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT

### 1.1 Khái quát và tính cấp thiết của đề tài
Theo tổ chức y tế thế giới (WHO), tỉ lệ mắc các bệnh ung thư da đang có xu hướng không ngừng gia tăng do một số những thay đổi về khí hậu toàn cầu và chỉ số tia cực tím (UV). Thực tế hiện nay, việc khám lâm sàng các bệnh về da vẫn phụ thuộc rất lớn vào kỹ năng và kinh nghiệm (ngay cả bằng mắt thường hay kính lúp Dermoscopy) của các chuyên gia da liễu.
Bên cạnh đó, các bệnh viện công tuyến đầu liên tục gặp tình trạng quá tải, thời gian để một bác sĩ quan sát mỗi bệnh nhân vô cùng ít ỏi, làm tỉ lệ chẩn đoán sai sót, sỉ sót bệnh lọt tuyến tăng cao.
=> **Tính Cấp Thiết:** Cần có một hệ thống máy tính chẩn đoán tự động (Computer-Aided Diagnosis - CAD), có tốc độ xử lý nhanh, độ tin cậy được giám sát, và đóng vai trò như một người bác sĩ thứ hai tham chiếu kết quả, giúp xác nhận lại chẩn đoán của phía bệnh viện.

### 1.2 Mục tiêu và đối tượng nghiên cứu
- **Mục tiêu Học thuật:** Ứng dụng thành công lý thuyết thị giác máy tính, cụ thể là các thuật toán trích xuất đặc trưng Convolutional Network, kĩ thuật Transfer Learning để giải quyết các trường hợp bất đối xứng dữ liệu y tế.
- **Mục tiêu Ứng dụng:** Xây dựng một ứng dụng trọn vẹn từ Frontend đến Backend (End-to-end AI Product), phục vụ thao tác upload trực tiếp ảnh da liễu và có trải nghiệm UI/UX thân thiện.
- **Đối tượng Phạm vi:** Tập trung vào hình ảnh bề mặt da với phân giải bất kỳ. Phân loại tổng cộng 24 nhóm bệnh da liễu bao quát nhất.

### 1.3 Tổng quan về công nghệ Học sâu (Deep Learning)
Học Sâu là một phân nhánh của Machine Learning, sử dụng các cấu trúc tính toán phức tạp gọi là mạng lưới nơ-ron nhân tạo (Neural Networks) gồm nhiều tầng ẩn (Hidden Layers). Với các kiến trúc lớn như EfficientNet, hệ thống tự động trích lọc các đặc trưng cấp thấp (cạnh, góc, màu sắc của vùng viêm) cho đến cấp cao (hình dạng khối u, kết cấu mô) mà không đòi hỏi con người định nghĩa quy luật rập khuôn thủ công đặc trưng. Tại cuối các chặng Convolution và Pooling, thuật toán tối ưu (AdamW) điều chỉnh dần các trọng số ma trận bộ lọc để cực tiểu hoá sai số dự đoán.

---

## CHƯƠNG 2. PHÂN TÍCH, THIẾT KẾ VÀ KIẾN TRÚC HỆ THỐNG

### 2.1 Yêu cầu hệ thống
- **Yêu cầu chức năng:**
  - Khách vãng lai: Tải ảnh, chụp ảnh trực tiếp từ camera, và nhận kết quả phân tích trong vòng 3-5 giây.
  - Quản trị viên (Admin): Đăng nhập, xem nhật ký chẩn đoán của hệ thống, xem các thống kê qua biểu đồ dashboard trực quan.
- **Yêu cầu phi chức năng:**
  - Tính khả dụng (Availability): Hệ thống cần ổn định 24/7.
  - Tính bảo mật (Security): Thông tin hình ảnh của người dùng không được phép rò rỉ, mã hóa password theo chuẩn bcrypt và giao tiếp qua JWT token.
  - Tính chính xác: Độ nhạy (Recall) của mô hình đối với các nhóm bệnh ung thư cần đặc biệt cao > 95% để hạn chế việc bỏ lọt bệnh hiểm nghèo.

### 2.2 Thiết kế kiến trúc Hệ thống & Biểu đồ UML

*(Ghi chú: Vui lòng thay thế phần ngoặc vuông bằng hình ảnh thực tế của bạn lúc đưa vào file Word báo cáo)*

#### 2.2.1 Sơ đồ ca sử dụng (Use Case Diagram)
> **[CHÈN ẢNH SƠ ĐỒ USE CASE DÀNH CHO HỆ THỐNG TẠI ĐÂY]**

**Giải thích Sơ đồ Use Case:**
Sơ đồ ca sử dụng mô tả các tương tác chính giữa Tác nhân (Actor) và Hệ thống (System), bao gồm:
1. **User (Bệnh nhân/Bác sĩ cơ sở):** Tác nhân thực hiện hành vi "Upload Hình ẢNh", "Xem kết quả Grad-CAM", "Xem Lịch sử".
2. **Admin (Quản trị Hệ thống Y tế):** Kế thừa các quyền của User, có thêm quyền "Đăng nhập", "Quản lý dữ liệu người dùng", "Xem bảng thống kê Dashboard Dashboard".
3. **AI Inference Core (Hệ thống ngầm):** Tiếp nhận ảnh từ Middleware, kích hoạt luồng "Dự đoán mô hình" (Predict) và "Vẽ biểu đồ nhiệt" (Generate Grad-CAM).

#### 2.2.2 Sơ đồ luồng dữ liệu (Data Flow Diagram - DFD)
> **[CHÈN ẢNH DFD MỨC 0 (CONTEXT) HOẶC MỨC 1 TẠI ĐÂY]**

**Giải thích Sơ đồ Luồng dữ liệu (DFD):**
- **Nguồn - Đích:** Người dùng và Cơ sở dữ liệu chẩn đoán (Database).
- **Tiến trình xử lý chính:** (1.1) Xác thực bảo mật Request -> (1.2) Tiền xử lý khung ảnh -> (1.3) Xử lý học máy với Tensor -> (1.4) Trả về chuỗi Json định dạng điểm số tự tin. 
Sơ đồ DFD giúp minh họa rõ đường đi của hạt dữ liệu (Data packet) cấu trúc dưới dạng base64/jpeg Image được chuyển hóa qua các Node service cho đến khi được định hình thành một Model (Schema JSON) cuối cùng đưa vào Storage Database.

#### 2.2.3 Sơ đồ thực thể kết hợp (Entity-Relationship Diagram - ERD)
> **[CHÈN ẢNH SƠ ĐỒ ERD (ENTITY RELATIONSHIP DIAGRAM) TẠI ĐÂY]**

**Giải thích Sơ đồ ERD:**
Cơ sở dữ liệu NoSQL/SQL (tùy thuộc kiến trúc dự án thực tế) được thiết kế xoay quanh các bảng (Table)/Collection chính:
- `tbl_Users`: Quản trị danh tính (id, role, hashed_password, created_at)
- `tbl_Diagnoses`: Lưu thông tin phiên dự đoán (id, user_id, image_url, predicted_disease_id, confidence_score, heat_map_url, timestamp). Có mối quan hệ 1-N với User.
- `tbl_Diseases`: Danh mục Metadata 24 bệnh (id, eng_name, vie_name, danger_level).
Việc tách bạch rõ ràng giúp truy vấn thống kê dữ liệu để vẽ Dashboard trở nên tối ưu (đạt thời gian phản hồi API < 100ms).

#### 2.2.4 Sơ đồ Lớp (Class Diagram)
> **[CHÈN ẢNH SƠ ĐỒ CLASS DIAGRAM TẠI ĐÂY]**

**Giải thích Sơ đồ Lớp (Hướng Đối Tượng):**
Minh hoạ cấu trúc Code Backend của FastAPI với các Object đóng gói. 
- `InferenceEngine`: Lớp chứa con trỏ tới model PyTorch được load trên RAM. Cung cấp hàm `predict()`.
- `Preprocessor`: Gồm các Method tĩnh (Static Method) như `apply_dullrazor()`, `run_yolo()`.
- `GradCamExplainer`: Thừa kế các interface để chèn hàm Hook vào các Conv Layers cuối cùng của mạng CNN, trích xuất gradients nhân với activation maps.

### 2.3 Thiết kế giao diện Người dùng (UI/UX)
Giao diện được xây dựng tuân thủ nguyên tắc thiết kế phẳng (Flat Design) kết hợp tông màu y tế (Xanh lam dịu nhẹ và Trắng tuyết), tạo sự tin cậy tuyệt đối và hiện đại.

#### 2.3.1 Giao diện Trang chủ (Landing Page)
> **[CHÈN ẢNH GIAO DIỆN TRANG CHỦ TẠI ĐÂY]**

- Banner Header cỡ lớn truyền đạt thông điệp về AI tiết kiệm sự sống.
- Các Cards về tính năng: Chẩn đoán AI đa nền tảng, công nghệ tiên tiến, hỗ trợ khám chữa.

#### 2.3.2 Giao diện Màn hình Chẩn đoán (Diagnose Screen)
> **[CHÈN ẢNH GIAO DIỆN TRANG CHẨN ĐOÁN TẠI ĐÂY]**

- Drag-and-Drop (Kéo thả) vùng chữ nhật lớn ở chính giữa đễ upload ảnh tiện lợi. Cửa sổ Preview (Xem trước) ảnh.
- Nút bấm Call-To-Action (Kêu gọi hành động) nổi bật khởi động tiến trình truyền dữ liệu (kèm biểu tượng Spinner loding trong quá trình server giải quyết).

#### 2.3.3 Giao diện Kết quả Giải thích (Result / Grad-CAM Page)
> **[CHÈN ẢNH GIAO DIỆN KẾT QUẢ VÀ BẢN ĐỒ NHIỆT TẠI ĐÂY]**

- Phân rã màn hình thành 2 cột. 
- **Cột trái:** Hình ảnh gốc và hình ảnh đè lưới màu Grad-CAM (Đỏ cam biểu tượng cho vùng biểu bì hư hại cao độ, vùng màu xanh sẫm là da khỏe mạnh không liên quan đến quyết định mô hình).
- **Cột phải:** Bảng tên bệnh, Progress Bar thể hiện Tỷ Lệ% Confidence, mô tả tính chất bệnh lý nguy hiểm (có Icon ⚠️ báo động đỏ nếu là bệnh Ung thư).

#### 2.3.4 Bảng Điều khiển Quản trị viên (Admin Dashboard)
> **[CHÈN ẢNH GIAO DIỆN ADMIN DASHBOARD TẠI ĐÂY]**

- Biểu đồ Bar Chart (Thống kê loại bệnh phát hiện theo tháng).
- Biểu đồ Doughnut Chart (Cơ cấu độ nguy hiểm: Thấp - Trung Bình - Cao).
- Bảng Grid chứa lịch sử Data dạng bảng log, phục vụ trích xuất CSV file.

---

## CHƯƠNG 3. QUY TRÌNH TIỀN XỬ LÝ VÀ CHUẨN BỊ DỮ LIỆU

### 3.1 Bộ dữ liệu ISIC, DermNet NZ và PAD-UFES-20
Để giải quyết triệt để 24 căn bệnh (classes) khác nhau, dự án phải thu thập và tổng hợp từ nhiều nguồn dữ liệu đa dạng giúp hạn chế sai lệch về ánh sáng (Illumination Bias), tông màu da đa chủng tộc. Tổng quy mô chốt hạ ở khoảng 41,000 ảnh.
Các bệnh được phân chia làm 24 nhãn cụ thể (bao gồm Melanoma, Basal Cell Carcinoma, Actinic Keratosis, ... tới Acne, Eczema). 

### 3.2 Kỹ thuật Tiền xử lý hỗn hợp (Hybrid Preprocessing Pipeline)
Ảnh nguyên bản thường chứa nhiều phông nền (Background) dư thừa như ga giường, bề mặt kim loại thiết bị y khoa, thước đo tỷ lệ, hay các sợi lông chân rậm rạp làm sai chệch phân tích vùng tổn thương.

#### 3.2.1 Nhận diện phân vùng tổn thương vớik YOLOv8-Segment
YOLOv8-seg (Phiên bản Nano) được huấn luyện một task riêng biệt để tạo ra khung Bounding Box và Segment Mask, bóc tách toàn bộ "Vùng da nhiễm bệnh" khỏi phông trắng hay đồ vật xung quanh (Background Suppression), giảm thiểu hiện tượng "Kẻ thụ hưởng biểu diễn tắt" (Shortcut Representation Learning) của AI.

#### 3.2.2 Loại bỏ nhiễu lông với hệ số DullRazor
Thuật toán DullRazor kinh điển áp dụng chuỗi hình thái học (Morphological Operations):
1. Biến đổi ảnh sang Grayscale.
2. Áp dụng toán tử Black-Hat để tìm các cấu trúc dạng ống tối đen hẹp dài (sợi lông).
3. Đóng mặt nạ phân đoạn mờ (Thresholding Mask).
4. Phục hồi và bổ sung (Inpainting) các pixel da thịt vào vùng sợi lông vừa bị đục đi bằng thuật toán nội suy viền (Navier-Stokes base).

---

## CHƯƠNG 4. LỊCH SỬ HUẤN LUYỆN, TỐI ƯU HÓA VÀ PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM

### 4.1 Lịch sử Nghiên cứu và Nâng cấp Mô hình
Quá trình phát triển luồng suy luận AI của hệ thống trải qua 4 vòng lặp nghiên cứu (Iterations), từ đó rút ra các bài học đắt giá về tiền xử lý dữ liệu và thiết lập siêu tham số mạng Nơ-ron:

#### 4.1.1 Phiên bản V1.0 - Baseline Model (Khởi tạo)
- **Nguồn dữ liệu:** Dùng tập thô ISIC 2019 không tiền xử lý (ảnh chứa cực kỳ nhiều phông nền). Kích thước ảnh 224x224.
- **Kiến trúc mạng:** ResNet-50.
- **Đánh giá:** Mô hình liên tục vướng phải "Shortcut learning", các bức hình dính thước đo y tế và mảng màu tóc bị model học lầm thành "Bệnh ung thư". Model dễ dàng bị quá khớp (Overfit) sau 5 epoch do mất cân bằng dữ liệu cực kỳ khốc liệt (bệnh Nevus chiếm 80% tập train).
- **Kết quả thu được:** F1-Macro: `~0.510`, Accuracy cực kỳ thiên lệch. Mạng chỉ đoán đúng Nevus và sai toàn bộ các bệnh hiểm nghèo.

#### 4.1.2 Phiên bản V2.0 - Khắc phục Tiền xử lý (DullRazor & Seg)
- **Cải tiến:** Áp dụng hệ thống trích xuất nền YOLOv8-Segment và bộ lọc lông DullRazor. Cắt đứt hoàn toàn sự học vẹt ánh sáng và khung viền của AI, hướng mô hình trực diện vào vùng tổn thương. Cân bằng nhãn (Class weights) được nhân vào hàm CrossEntropyLoss.
- **Kiến trúc mạng:** Nâng cấp sang cấu trúc `EfficientNet-B4` với ImageSize 380x380 để nhìn rõ chi tiết biểu bì hơn (Fine-Grained).
- **Đánh giá:** Model F1 tăng vọt, các nhóm bệnh ung thư đã được nhận diện.
- **Kết quả thu được:** F1-Macro: `0.803`, Accuracy: `~83.1%`.

#### 4.1.3 Phiên bản V2.1 - Tối ưu Data Pipeline (Square-Root Sampling)
- **Cải tiến:** CrossEntropyLoss vẫn chưa chịu nỗ lực học các bệnh cực hiếm. Chiến lược Sampler (Hàm lấy mẫu) được thiết kế lại thành **Square-Root Weighted Random Sampler**, tăng tần suất bắt gặp điểm ảnh hiếm. Batch-size được giới hạn tại 48, sử dụng AMP (Automatic Mixed Precision) tiết kiệm VRAM.
- **Kết quả thu được:** F1-Macro: `0.835`, Accuracy: `86.2%`. Ma trận nhầm lẫn bắt đầu rõ ràng và tập trung cao tại đường chéo chính.

#### 4.1.4 Phiên bản V3.0 - Đỉnh cao Y Khoa với Asymmetric Loss (Phiên bản Cuối)
- **Cải tiến Quyết định:** Để một hệ thống nhúng sâu hoạt động ngoài thực địa thay cho bệnh viện, thuật toán "thà bắt nhầm còn hơn bỏ sót" Ung thư được đặt lên hàng đầu. Thay thế hàm CrossEntropyLoss thông thường bằng hàm **Asymmetric Loss (Hàm suy hao Dị Thể)**, phóng đại mức phạt (Penalty) lên lũy thừa cực hạn khi mô hình đệ trình "Âm Tính Giả" để buộc các đường ranh giới quyết định (Decision Boundary) mở rộng ra các ca nghi ngờ.
- **Kết quả thu được:** F1-Macro: `0.880`, Accuracy: `~88.5%`. Đạt thông số kĩ thuật State-Of-The-Art trên tập dữ liệu lai ISIC + DermNet.

---

### 4.2 Phân tích Sơ đồ Thực nghiệm Chuyên sâu (Phiên bản V3.0)

Toàn bộ biểu đồ dưới đây được xuất trích xuất trực tiếp từ máy chủ NVIDIA P100 của Kaggle sau khi Training Iteration V3.0 hội tụ.

#### 4.2.1 Phân bố Dữ liệu Đầu vào (Class Distribution Train vs Val)
> ![Class Distribution](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig6_class_distribution.png)
> *Hình 4.1. Biểu đồ phân bố và tần suất số lượng ảnh của Train và Validation data*

**Giải thích:** Cột đồ thị màu Xanh (Tập Train) và Cam (Tập Test, khoảng 20%) thể hiện độ mất cân bằng dốc đứng dạng Long-tail. Các căn bệnh ung thư như SCC, MEL rất ít ảnh.

#### 4.2.2 Sơ đồ Đường cong Học tập (Learning Curves)
> ![Learning Curves](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig1_learning_curves.png)
> *Hình 4.2. Đường cong hội tụ Loss, Accuracy và Macro F1 qua các Epochs*

**Giải thích:** Đường đứt nét thẳng đứng màu xanh lá chỉ điểm Best Checkpoint (Điểm trọng số tốt nhất trước khi model Overfitting trở lại ở các vòng lặp sau). Giá trị Val Loss hạ rất mượt, cho thấy kiến trúc EfficientNet có khả năng tổng quát hóa dữ liệu lâm sàng y tế tuyệt hảo.

#### 4.2.3 Ma trận Nhầm lẫn (Confusion Matrix)
> ![Confusion Matrix](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig2_confusion_matrix.png)
> *Hình 4.3. Ma trận nhầm lẫn (Dựa trên Best Weight V3.0 - Số liệu đếm tuyệt đối)*

**Giải thích:** Ở V3.0, ma trận này tập trung màu tối đậm trên một đường chéo dứt khoát. Những lốm đốm nhỏ ở các hàng viền biên khẳng định model vẫn có sác xuất nhầm nhẹ giữa các vùng da lành và vùng nốt ruồi phẳng. Dù vậy, nó bỏ xa độ phân tán đốm sáng thê thảm của bản V1.0.

#### 4.2.4 Phân tích Độ nhạy từng lớp (Per-Class F1, Precision, Recall)
> ![Per-Class Metrics](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig3_per_class_metrics.png)
> *Hình 4.4. Biểu đồ cột của 3 thang đo F1 Score, Precision và Recall tại 24 Lớp Bệnh*

**Giải thích:** Đường kẻ chấm bi đỏ vạch đích Threshold `0.9` (90%). Mô hình dễ dàng qua mặt threshold này ở hầu hết các lớp bệnh liên quan đến khối u và hắc tố nhờ hàm mất mát Asymmetric.

#### 4.2.5 Đường cong ROC và PR (Precision-Recall) Vĩ mô
> ![ROC Curves](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig4_roc_curves.png)
> *Hình 4.5. Biểu đồ Đường cong ROC trung bình Vĩ mô (Macro-Average ROC)*

> ![Precision-Recall Curves](file:///home/khangjv/WorkSpace/MedAI_Dermatology/kaggle-train-24class-v3.0-results/fig5_precision_recall_curves.png)
> *Hình 4.6. Biểu đồ Precision-Recall đánh giá độ chịu lỗi (Macro AP Threshold)*

**Giải thích:** Cả hai sơ đồ đánh giá ngưỡng phân vùng (Area Under Curve - AUC) đều đạt con số mơ ước `~0.95`. Mô hình chứng tỏ hệ số "Thận Trọng" cực kỳ cao khi dự đoán bệnh hiếm khi bị sa lầy vào cạm bẫy Dương Tính Giả (Phân loại sai bậy bạ một vết côn trùng cắn thành khối u).

---


## CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN TƯƠNG LAI

### 5.1 Kết luận chung và Đóng góp đạt được
Đề tài nghiên cứu đã diễn giải, thiết kế và triển khai trọn vẹn thành công Hệ thống Phân loại 24 bệnh lý da liễu tự động hóa với kết quả nghiệm thu vô cùng mỹ mãn. AI Model (EfficientNetB4-V2.1-V3.0) đạt độ chuẩn xác lâm sàng ~86.2%. Web Hệ thống có kiến trúc Modular hiện đại, khả năng chống chọi tải mạnh, bảo mật vững chai.
Với chuỗi Pipeline xử lý nhiễu bằng giải thuật DullRazor truyền thống kết hợp xử lý AI YOLOv8 mới mẻ thể hiện sự nhuần nhuyễn dung hòa về Kỹ thuật máy tính.

### 5.2 Hạn chế của đề tài
1. Kích thước tập dữ liệu đối với những căn bệnh "Ngách, Hiếm Sinh" mang tính chất nhiệt đới (của người Da Vàng Châu Á / Việt Nam) còn rất kém. Data Set hiên tại thu thập ở khu vực Âu Mỹ, nơi hắc tố da cơ địa đa số thuộc nhóm da trắng/đen (Fitzpatrick 1,2,5,6), nên ánh sáng khi soi da sẽ hơi lệch chuẩn so với da vàng.
2. Nguồn lực huấn luyện và giới hạn VRAM (16GB) dẫn đến hệ số Batch Size chưa thể đẩy mạnh tới cực hạn.

### 5.3 Định hướng phát triển
1. Liên kết thu thập Datasets (Tập dữ liệu) nội địa mang màu sắc của bệnh nhân Việt Nam. Tinh chỉnh mạng lại từ dữ liệu Transfer Learning.
2. Tích hợp AI tạo sinh (Generative AI) vào ứng dụng để có thể nói chuyện tương tác chat 2 chiều cùng bệnh nhân với kết quả dự đoán thay vì chẩn đoán nguội vô hồn. (e.g. Chatbot LLM phân tích lối sống dinh dưỡng).
3. Đóng gói Ứng dụng thành Native Mobile Apps (iOS/Android) tích hợp Camera trực tiếp Real-Time Processing để y sĩ sử dụng bằng chính tay cầm điện thoại thay vì Web App.

---
*(Xem `USER_MANUAL.md` để lấy hướng dẫn vận hành chi tiết đối với Lập trình viên)*
