
import os
import sys
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras import optimizers, callbacks
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.efficientnet import preprocess_input
from sklearn.utils.class_weight import compute_class_weight

# Thêm thư mục gốc vào path để tìm được modules
sys.path.append(os.path.abspath(os.getcwd()))

from src.models.efficientnet_clf import build_model

def get_args():
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình EfficientNet-B3 để phân loại bệnh da liễu")
    parser.add_argument("--epochs", type=int, default=50, help="Số lượng epochs Phase 1 (Frozen)")
    parser.add_argument("--finetune_epochs", type=int, default=20, help="Số lượng epochs Phase 2 (Fine-tuning)")
    parser.add_argument("--batch_size", type=int, default=32, help="Kích thước batch")
    parser.add_argument("--lr", type=float, default=1e-4, help="Tốc độ học Phase 1")
    parser.add_argument("--finetune_lr", type=float, default=1e-5, help="Tốc độ học Phase 2 (Fine-tuning)")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Đường dẫn đến thư mục dữ liệu đã xử lý")
    parser.add_argument("--model_save_path", type=str, default="models/efficientnet_b3.h5", help="Đường dẫn để lưu mô hình")
    parser.add_argument("--dry_run", action="store_true", help="Chạy thử nhanh 1 epoch (mỗi phase) để kiểm tra lỗi code")
    return parser.parse_args()

def train(args):
    print(f"Phiên bản TensorFlow: {tf.__version__}")
    print(f"GPU khả dụng: {len(tf.config.list_physical_devices('GPU')) > 0}")

    IMG_SIZE = (300, 300)
    NUM_CLASSES = 7

    # --- 1. SETUP DATA GENERATORS (STRONG AUGMENTATION) ---
    print(f"\n📂 Đang tải dữ liệu từ {args.data_dir}...")
    
    train_dir = os.path.join(args.data_dir, 'train')
    val_dir = os.path.join(args.data_dir, 'val')
    test_dir = os.path.join(args.data_dir, 'test')

    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"Không tìm thấy thư mục train: {train_dir}")
    
    # Data augmentation MẠNH HƠN cho training set (Giống Kaggle)
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input, # EfficientNet native preprocessing
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        zoom_range=0.3,
        shear_range=0.2,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )

    # Chỉ preprocess cho val và test
    val_test_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input
    )

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=args.batch_size,
        class_mode='categorical',
        shuffle=True
    )

    val_generator = val_test_datagen.flow_from_directory(
        val_dir,
        target_size=IMG_SIZE,
        batch_size=args.batch_size,
        class_mode='categorical',
        shuffle=False
    )

    test_generator = val_test_datagen.flow_from_directory(
        test_dir,
        target_size=IMG_SIZE,
        batch_size=args.batch_size,
        class_mode='categorical',
        shuffle=False
    )

    # --- 2. COMPUTE CLASS WEIGHTS ---
    print("\n⚖️  Computing class weights...")
    class_weights = compute_class_weight(
        'balanced',
        classes=np.unique(train_generator.classes),
        y=train_generator.classes
    )
    class_weight_dict = dict(enumerate(class_weights))
    
    print("Class weights (fix imbalance):")
    for cls, idx in train_generator.class_indices.items():
        print(f"   {cls}: {class_weight_dict[idx]:.3f}")

    # --- 3. BUILD MODEL ---
    print("\n🏗️  Đang khởi tạo mô hình EfficientNet-B3...")
    model = build_model(num_classes=NUM_CLASSES, input_shape=(*IMG_SIZE, 3))
    
    # --- PHASE 1: TRANSFER LEARNING (FROZEN BASE) ---
    print("\n🚀 BẮT ĐẦU PHASE 1: Transfer Learning (Frozen Base)")
    
    optimizer = optimizers.Adam(learning_rate=args.lr)
    
    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    
    # Callbacks
    os.makedirs(os.path.dirname(args.model_save_path), exist_ok=True)
    
    checkpoint_cb = callbacks.ModelCheckpoint(
        args.model_save_path,
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    )
    
    early_stopping_cb = callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10, # Increased patience -> Aggressive training
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr_cb = callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=1
    )
    
    my_callbacks = [checkpoint_cb, early_stopping_cb, reduce_lr_cb]

    # Config dry run
    steps_per_epoch = None
    validation_steps = None
    epochs_phase1 = args.epochs
    epochs_phase2 = args.finetune_epochs
    
    if args.dry_run:
        print("⚠️ CHẾ ĐỘ DRURUN: 1 Epoch mỗi phase, 1 step mỗi epoch.")
        epochs_phase1 = 1
        epochs_phase2 = 1
        steps_per_epoch = 1
        validation_steps = 1

    # Train Phase 1
    history_phase1 = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=epochs_phase1,
        callbacks=my_callbacks,
        class_weight=class_weight_dict, # Sử dụng class weights
        steps_per_epoch=steps_per_epoch,
        validation_steps=validation_steps
    )
    
    # --- PHASE 2: FINE-TUNING ---
    print("\n🔧 BẮT ĐẦU PHASE 2: Fine-tuning (Unfreeze top layers)")
    
    # Set entire model to trainable first
    model.trainable = True
    
    # Freeze all layers EXCEPT the last 50
    # (Includes the new classification head layers)
    N_FINE_TUNE = 50
    
    for layer in model.layers[:-N_FINE_TUNE]:
        layer.trainable = False
        
    print(f"Trainable layers: {len([l for l in model.layers if l.trainable])}")
    
    # Recompile with lower LR
    model.compile(
        optimizer=optimizers.Adam(learning_rate=args.finetune_lr), # Lower LR
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    
    # Train Phase 2
    history_phase2 = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=epochs_phase2,
        callbacks=my_callbacks,
        class_weight=class_weight_dict,
        steps_per_epoch=steps_per_epoch,
        validation_steps=validation_steps
    )

    # --- EVALUATION ---
    print("\n📊 Đang đánh giá trên tập Test...")
    test_loss, test_acc, test_auc = model.evaluate(test_generator, steps=validation_steps)
    print(f"\n🏆 Độ chính xác trên tập Test: {test_acc*100:.2f}%")
    print(f"⭐ AUC Score: {test_auc:.4f}")
    
    if args.dry_run:
         print("✅ Chạy thử hoàn tất thành công!")


if __name__ == "__main__":
    args = get_args()
    train(args)

