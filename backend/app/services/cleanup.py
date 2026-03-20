"""
Dịch vụ dọn dẹp (Cleanup Service)
Tự động xóa các file ảnh cũ trong thư mục uploads để tiết kiệm dung lượng đĩa.
"""
import os
import time
import logging
from pathlib import Path
from .config import settings

logger = logging.getLogger(__name__)

def cleanup_old_uploads(max_age_seconds: int = 3600):
    """
    Xóa các file trong thư mục uploads có tuổi thọ lớn hơn max_age_seconds.
    Mặc định: 1 giờ (3600 giây).
    """
    if not settings.UPLOAD_DIR.exists():
        return

    now = time.time()
    count = 0
    try:
        for file_path in settings.UPLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
                file_age = now - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    count += 1
        
        if count > 0:
            logger.info(f"🧹 Cleanup: Removed {count} old temporary images.")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

async def run_cleanup_periodically(interval_seconds: int = 1800):
    """
    Chạy dọn dẹp định kỳ (mặc định 30 phút).
    Dùng trong Background Task của FastAPI.
    """
    import asyncio
    while True:
        cleanup_old_uploads()
        await asyncio.sleep(interval_seconds)
