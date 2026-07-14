"""占卜记录模型"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    spread_id: Mapped[int] = mapped_column(Integer, ForeignKey("spreads.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: [{"position":1,"position_name":"过去","card_name":"愚者","is_reversed":false}]
    cards_drawn: Mapped[str] = mapped_column(Text, nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI解读全文
    share_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI分享摘要
    share_code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)  # 分享码
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="readings")
    spread: Mapped["Spread"] = relationship("Spread", back_populates="readings")
