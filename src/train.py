import os
import sys
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras import optimizers, callbacks
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from sklearn.utils.class_weight import compute_class_weight

IMG_SIZE = (300, 300) # Kích thước chuẩn cho EfficientNetB3
NUM_CLASSES = 8       # MEL, NV, BCC, AK, BKL, DF, VASC, SCC

def get_args():
    parser = argparse.ArgumentParser(description="Huấn luyện EfficientNet-B3 (ISIC 2019 - 8 Classes)")
    
    # Các tham số có thể thay đổi khi chạy lệnh
    parser.add_argument("--epochs", type=int, default=50, help="Số lượng Epochs tối đa")
    parser.add_argument("--batch_size", type=int, default=32, help="Kích thước Batch")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning Rate ban đầu")
    
    # Đường dẫn dữ liệu và nơi lưu model
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Folder dữ liệu đã tiền xử lý")
    parser.add_argument("--model_save_path", type=str, default="models/efficientnet_b3_isic.keras", help="Đường dẫn lưu model")
    
    return parser.parse_args()

def build_efficientnet_model(num_classes):
    """
    Xây dựng kiến trúc model:
    EfficientNetB3 (Frozen) + Custom Head (Classification)
    """
    # 1. Tải Base Model
    base_model = EfficientNetB3(
        weights='imagenet', 
        include_top=False, 
        input_shape=(*IMG_SIZE, 3)
    )
    
    # Đóng băng Base Model
    base_model.trainable = False 

    # 2. Thêm các lớp Classification Head
    x = base_model.output
    x = GlobalAveragePooling2D()(x) # Biến đổi feature map thành vector
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)             # Giảm Overfitting
    x = Dense(512, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)
    
    # Lớp Output: 8 neuron cho 8 loại bệnh
    outputs = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=outputs)
    return model

def train(args):
    # --- 0. SETUP GPU ---
    # Cấu hình để tránh lỗi tràn bộ nhớ (OOM)
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"✅ Đã tìm thấy {len(gpus)} GPU: {[gpu.name for gpu in gpus]}")
        except RuntimeError as e:
            print(e)
    else:
        print("⚠️ Không tìm thấy GPU, quá trình train sẽ rất chậm!")

    # --- 1. DATA GENERATORS ---
    print(f"\n📂 Đang tải dữ liệu từ: {args.data_dir}")
    
    train_dir = os.path.join(args.data_dir, 'train')
    val_dir = os.path.join(args.data_dir, 'val')

    if not os.path.exists(train_dir) or not os.path.exists(val_dir):
        print(f"❌ LỖI: Không tìm thấy thư mục 'train' hoặc 'val' trong {args.data_dir}")
        return

    # Augmentation cho tập Train
    train_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.efficientnet.preprocess_input,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        zoom_range=0.2,
        shear_range=0.2,
        fill_mode='nearest'
    )

    # Chỉ Preprocess cho tập Val
    val_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.efficientnet.preprocess_input
    )

    print("   Loading Train set...")
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=args.batch_size,
        class_mode='categorical',
        shuffle=True
    )

    print("   Loading Val set...")
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=IMG_SIZE,
        batch_size=args.batch_size,
        class_mode='categorical',
        shuffle=False
    )

    # Kiểm tra số lớp thực tế
    detected_classes = len(train_generator.class_indices)
    print(f"🔍 Phát hiện {detected_classes} lớp bệnh: {list(train_generator.class_indices.keys())}")
    
    if detected_classes != NUM_CLASSES:
        print(f"⚠️ CẢNH BÁO: Code mong đợi {NUM_CLASSES} lớp, nhưng dữ liệu có {detected_classes} lớp.")

    # --- 2. TÍNH TOÁN CLASS WEIGHTS ---
    print("\n⚖️  Đang tính toán Class Weights (Chống mất cân bằng dữ liệu)...")
    try:
        class_weights = compute_class_weight(
            class_weight='balanced',
            classes=np.unique(train_generator.classes),
            y=train_generator.classes
        )
        # Chuyển về dictionary cho Keras
        class_weight_dict = dict(enumerate(class_weights))
        print("   ✅ Trọng số đã tính:", {k: round(v, 2) for k, v in class_weight_dict.items()})
    except Exception as e:
        print(f"⚠️ Lỗi khi tính class weights: {e}")
        class_weight_dict = None

    # --- 3. KHỞI TẠO MODEL ---
    print("\n🏗️  Đang xây dựng model EfficientNetB3...")
    model = build_efficientnet_model(detected_classes)
    
    optimizer = optimizers.Adam(learning_rate=args.lr)
    
    model.compile(
        optimizer=optimizer, 
        loss='categorical_crossentropy', 
        metrics=['accuracy']
    )

    # --- 4. CALLBACKS ---
    os.makedirs(os.path.dirname(args.model_save_path), exist_ok=True)
    
    callbacks_list = [
        # Lưu model tốt nhất (theo val_accuracy)
        callbacks.ModelCheckpoint(
            args.model_save_path, 
            monitor='val_accuracy', 
            save_best_only=True, 
            mode='max', 
            verbose=1
        ),
        # Dừng sớm nếu val_loss không giảm sau 10 epoch
        callbacks.EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True, 
            verbose=1
        ),
        # Giảm learning rate nếu kẹt
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', 
            factor=0.2, 
            patience=3, 
            min_lr=1e-6, 
            verbose=1
        )
    ]

    # --- 5. TRAINING ---
    print(f"\n🚀 BẮT ĐẦU TRAINING ({args.epochs} Epochs)...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=args.epochs,
        callbacks=callbacks_list,
        class_weight=class_weight_dict
    )
    
    print(f"\n✅ HUẤN LUYỆN HOÀN TẤT!")
    print(f"💾 Model đã được lưu tại: {args.model_save_path}")

if __name__ == "__main__":
    args = get_args()
    train(args)