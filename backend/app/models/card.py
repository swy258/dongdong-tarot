"""78张塔罗牌模型"""
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_zh: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # 中文名
    name_en: Mapped[str] = mapped_column(String(100))  # 英文名
    card_type: Mapped[str] = mapped_column(String(20))  # major(大阿尔卡纳) / minor(小阿尔卡纳)
    suit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 权杖/圣杯/宝剑/星币 (小阿尔卡纳)
    number: Mapped[int] = mapped_column(Integer)  # 牌面数字(大阿尔卡纳0-21, 小阿尔卡纳1-14)
    keywords: Mapped[str] = mapped_column(Text)  # 关键词，逗号分隔
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # 简要描述
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 图片URL(可选)
