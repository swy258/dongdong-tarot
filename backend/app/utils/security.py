"""安全工具：密码哈希 + JWT"""
from datetime import datetime, timedelta
import hashlib
import secrets

from jose import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 哈希密码（避免passlib/bcrypt兼容性问题）"""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,
    ).hex()
    return f"{salt}${pw_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        salt, pw_hash = hashed_password.split('$', 1)
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000,
        ).hex()
        return secrets.compare_digest(computed_hash, pw_hash)
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        return None
