import os
import sys
import subprocess
import time
import webbrowser
import platform
from pathlib import Path

# --- CẤU HÌNH ---
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
VENV_DIR = BASE_DIR / ".venv"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
    if platform.system() == "Windows":
        try:
            import colorama
            colorama.init()
        except ImportError:
            HEADER = BLUE = GREEN = WARNING = FAIL = ENDC = ''

def log(message, level="info"):
    if level == "info":
        print(f"{Colors.BLUE}[INFO] {message}{Colors.ENDC}")
    elif level == "success":
        print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.ENDC}")
    elif level == "error":
        print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")
    elif level == "warning":
        print(f"{Colors.WARNING}[WARNING] {message}{Colors.ENDC}")

def get_venv_python():
    """Lấy đường dẫn python trong venv tùy theo hệ điều hành"""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def check_and_create_venv():
    """Kiểm tra và tạo virtual environment nếu chưa có"""
    if not VENV_DIR.exists():
        log("Chưa tìm thấy môi trường ảo (.venv). Đang tạo mới...", "warning")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
            log("Đã tạo môi trường ảo thành công.", "success")
        except subprocess.CalledProcessError:
            log("Không thể tạo .venv. Vui lòng kiểm tra cài đặt Python.", "error")
            sys.exit(1)
    else:
        log("Môi trường ảo (.venv) đã tồn tại.", "success")

def check_and_install_requirements():
    """Cài đặt thư viện vào trong venv"""
    venv_python = get_venv_python()
    req_file = BACKEND_DIR / "requirements.txt"

    if not req_file.exists():
        log("Không tìm thấy file backend/requirements.txt.", "error")
        return

    log("Đang kiểm tra và cài đặt thư viện (trong .venv)...")
    try:
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", str(req_file)])
        log("Cài đặt thư viện hoàn tất.", "success")
    except subprocess.CalledProcessError as e:
        log(f"Lỗi khi cài đặt thư viện: {e}", "error")
        sys.exit(1)

def run_system():
    processes = []
    venv_python = get_venv_python()
    
    try:     
        # 1. Chuẩn bị môi trường
        check_and_create_venv()
        check_and_install_requirements()

        # 2. Start Backend
        log(f"Đang khởi động Backend server (Port {BACKEND_PORT})...")
        
        backend_cmd = [
            str(venv_python), "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", str(BACKEND_PORT)
        ]
        
        # Set PYTHONPATH để backend có thể import module preprocessing
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BASE_DIR)
        
        backend_process = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=env)
        processes.append(backend_process)
        
        log("Đợi 5 giây cho Backend khởi động...", "info")
        time.sleep(5) 

        # 3. Start Frontend
        log(f"Đang khởi động Frontend server (Port {FRONTEND_PORT})...")
        frontend_cmd = [str(venv_python), "-m", "http.server", str(FRONTEND_PORT)]
        
        frontend_process = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)
        processes.append(frontend_process)

        print("\n" + "="*50)
        log("✅ HỆ THỐNG ĐÃ SẴN SÀNG SỬ DỤNG!", "success")
        log(f"👉 Backend API:    http://localhost:{BACKEND_PORT}")
        log(f"👉 API Swagger:    http://localhost:{BACKEND_PORT}/docs")
        log(f"👉 Frontend Web:   http://localhost:{FRONTEND_PORT}")
        print("="*50 + "\n")
        log("📌 Frontend sẽ gọi API tới localhost:8000 (xem config.js)")
        log("🛑 Nhấn Ctrl+C để dừng toàn bộ hệ thống.")

        # Tự động mở trình duyệt
        try:
            webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        except:
            pass

        # Giữ script chạy
        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\n")
        log("Đang dừng hệ thống...", "warning")
    except Exception as e:
        log(f"Lỗi không mong muốn: {e}", "error")
    finally:
        log("Đang dọn dẹp tiến trình...", "info")
        for p in processes:
            try:
                p.terminate()
            except:
                pass
        log("Tạm biệt! 👋", "success")

if __name__ == "__main__":
    if not sys.version_info >= (3, 10):
        print("Vui lòng sử dụng Python 3.10 trở lên.")
        sys.exit(1)
    run_system()
