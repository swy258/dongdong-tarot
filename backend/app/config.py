"""应用配置"""
import os
from pathlib import Path

from pydantic_settings import BaseSettings

# 计算基础路径
BASE_DIR = Path(__file__).resolve().parent.parent  # backend 目录


class Settings(BaseSettings):
    # 数据库 - 使用绝对路径
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'dongdong_tarot.db'}"

    # JWT
    SECRET_KEY: str = "dongdong-tarot-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 书籍文献目录 - 自动解析为绝对路径
    BOOKS_DIR: str = str(BASE_DIR.parent / "书籍文献")

    # 向量存储目录
    VECTOR_STORE_DIR: str = str(BASE_DIR / "vector_store")

    # PDF是否已处理
    PDF_PROCESSED: bool = False

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"


settings = Settings()
