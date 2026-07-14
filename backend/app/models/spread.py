"""牌阵模型"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Spread(Base):
    __tablename__ = "spreads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否预设牌阵
    positions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: [{"index":1,"name":"过去","meaning":"..."}]
    layout_type: Mapped[str | None] = mapped_column(String(30), nullable=True, default="grid")
    layout_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON坐标数据 用于自定义排布
    creator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped["User | None"] = relationship("User", back_populates="spreads")
    readings: Mapped[list["Reading"]] = relationship("Reading", back_populates="spread", lazy="dynamic")
