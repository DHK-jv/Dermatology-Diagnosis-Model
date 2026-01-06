MedAI_Dermatology/
│
├── data/                               # Quản lý dữ liệu
│   ├── raw/
│   │   ├── metadata.csv
│   │   └── images                      # Dữ liệu gốc (HAM10000 + metadata.csv)
│   ├── processed/                      # Ảnh sau tiền xử lý (DullRazor, Crop, Resize)
│   │    ├── roi/                       # Ảnh RGB đã crop theo mask
│   │    │   ├── train/
│   │    │   ├── val/
│   │    │   └── test/
│   │    │
│   │    └── metadata_clean.csv         # Metadata đã lọc (ảnh hợp lệ)
│   └── masks/                          # Mask segmentation cho U-Net
│       └── lesion/                     # Ảnh trắng–đen (.png/.jpg)
│
├── notebooks/                          # Jupyter Notebook (EDA & Training)
│   ├── 01_eda_data.ipynb               # Phân tích dữ liệu ban đầu
│   ├── 02_crop_roi.ipynb               # Cắt ROI từ mask
│   └── 03_train_model.ipynb            # Huấn luyện EfficientNet-B3
│
├── src/                                # Mã nguồn chính
│   │
│   ├── preprocessing/                  # Tiền xử lý ảnh
│   │   ├── dull_razor.py               # Xóa lông ảnh da (DullRazor)
│   │   └── image_cleaner.py            # Crop, Resize, Normalize
│   │
│   ├── models/                         # Kiến trúc mô hình
│   │   ├── unet_segmentor.py           # U-Net cho segmentation
│   │   └── efficientnet_clf.py         # EfficientNet-B3 cho classification
│   │
│   ├── fusion/                         # Tích hợp đa phương thức
│   │   └── feature_fusion.py           # Kết hợp ảnh + dữ liệu lâm sàng
│   │
│   ├── api/                            # Backend API (phần của Khang)
│   │   ├── main.py                     # Entry point FastAPI / Flask
│   │   └── ollama_client.py            # Kết nối Ollama (LLM khuyến nghị)
│   │
│   ├── utils/                          # CÔNG CỤ BỔ TRỢ
│   │   ├── logger.py                   # Ghi nhật ký quá trình huấn luyện/chạy API
│   │   └── medical_rules.py            # Logic luật suy luận y khoa (rule-based reasoning)
│   │
│   └── explainability/                 # Giải thích mô hình (XAI)
│       └── grad_cam.py                 # Grad-CAM heatmap
│
├── models_checkpoints/                 # Lưu trọng số mô hình (.h5 / .pth)
│
├── app/                                # Giao diện người dùng (Web/Mobile demo)
│
├── reports/                            # NƠI LƯU TRỮ KẾT QUẢ XUẤT RA
│   ├── figures/                        # Biểu đồ Accuracy/Loss, Confusion Matrix 
│   └── tables/                         # Các file .csv thống kê độ chính xác
│
├── requirements.txt                    # Danh sách thư viện
│
├── .gitignore                          # FILE LOẠI TRỪ
├── .env                                # Lưu các biến môi trường (như API Key, Port)
│
│
└── README.md                           # Hướng dẫn cài đặt & chạy dự án