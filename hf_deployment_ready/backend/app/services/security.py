import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

import secrets

# Để tạo ngẫu nhiên một chuỗi bảo mật cứng, hãy chạy: openssl rand -hex 32
# LƯU Ý MẠNH MẼ: Nếu không set biến môi trường JWT_SECRET_KEY ở HF Spaces production, hệ thống sẽ 
# tự random key mới mỗi lần Docker Reboot (khi file này load lại), làm mọi người dùng bị bắt Login lại.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)) # Mặc định là sống được 7 ngày

try:
    import bcrypt
    USE_RAW_BCRYPT = True
except ImportError:
    USE_RAW_BCRYPT = False

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác thực mật khẩu dạng văn bản thuần túy so với mật khẩu đã bị mã hóa (hashed)"""
    if USE_RAW_BCRYPT:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Tạo mã băm (bcrypt hash) cho mật khẩu"""
    if USE_RAW_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo một mã thông báo (token) truy cập JWT mới"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
