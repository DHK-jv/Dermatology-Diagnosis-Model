"""
TensorFlow Configuration Utility
Giải quyết vấn đề CUDA compatibility và cho phép chạy trên CPU khi cần
"""
import os
import tensorflow as tf

def setup_tensorflow(force_cpu=False, gpu_memory_limit=None):
    """
    Cấu hình TensorFlow để xử lý lỗi CUDA và tối ưu hóa
    
    Args:
        force_cpu (bool): Buộc sử dụng CPU thay vì GPU
        gpu_memory_limit (int): Giới hạn bộ nhớ GPU (MB), None = unlimited
    
    Returns:
        str: Device đang sử dụng ('CPU' hoặc 'GPU')
    """
    
    # Kiểm tra biến môi trường
    if os.environ.get('FORCE_CPU', '0') == '1':
        force_cpu = True
    
    # Nếu force CPU
    if force_cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        print("⚠️  TensorFlow đang chạy trên CPU mode")
        return 'CPU'
    
    # Cấu hình GPU
    try:
        gpus = tf.config.list_physical_devices('GPU')
        
        if gpus:
            print(f"✅ Phát hiện {len(gpus)} GPU(s)")
            
            for gpu in gpus:
                # Cho phép dynamic memory allocation
                tf.config.experimental.set_memory_growth(gpu, True)
                
                # Giới hạn memory nếu cần
                if gpu_memory_limit:
                    tf.config.set_logical_device_configuration(
                        gpu,
                        [tf.config.LogicalDeviceConfiguration(
                            memory_limit=gpu_memory_limit
                        )]
                    )
                    print(f"   GPU Memory limit: {gpu_memory_limit}MB")
            
            print("✅ TensorFlow đang chạy trên GPU mode")
            return 'GPU'
        else:
            print("⚠️  Không tìm thấy GPU, chuyển sang CPU mode")
            return 'CPU'
            
    except RuntimeError as e:
        # Lỗi CUDA - fallback về CPU
        print(f"⚠️  CUDA Error: {e}")
        print("⚠️  Tự động chuyển sang CPU mode")
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        return 'CPU'
    except Exception as e:
        print(f"⚠️  Unexpected Error: {e}")
        print("⚠️  Fallback to CPU mode")
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        return 'CPU'


def check_gpu_availability():
    """Kiểm tra GPU có khả dụng không"""
    try:
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"✅ GPU available: {len(gpus)} device(s)")
            for i, gpu in enumerate(gpus):
                print(f"   GPU {i}: {gpu.name}")
            return True
        else:
            print("❌ No GPU devices found")
            return False
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False


if __name__ == "__main__":
    print("=== TensorFlow GPU Check ===")
    print(f"TensorFlow version: {tf.__version__}")
    
    # Kiểm tra GPU
    has_gpu = check_gpu_availability()
    
    print("\n=== Setting up TensorFlow ===")
    device = setup_tensorflow()
    
    print(f"\n✅ TensorFlow is ready on: {device}")
