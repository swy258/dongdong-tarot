"""FastAPI 主入口"""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.database import engine, Base, SessionLocal
from app.models import User, Card, Spread, Reading
from app.routers import auth, cards, spreads, readings
from app.services.seed_data import get_card_seed_data, get_preset_spreads


def init_db():
    """初始化数据库：建表 + 种子数据"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        card_count = db.query(Card).count()
        if card_count == 0:
            print("Seeding 78 tarot cards...")
            for card_data in get_card_seed_data():
                card = Card(**card_data)
                db.add(card)
            db.commit()
            print("78 cards seeded successfully.")

        spread_count = db.query(Spread).filter(Spread.is_preset == True).count()
        if spread_count == 0:
            print("Seeding preset spreads...")
            for spread_data in get_preset_spreads():
                spread = Spread(**spread_data)
                db.add(spread)
            db.commit()
            print("Preset spreads seeded successfully.")

    finally:
        db.close()


app = FastAPI(
    title="东东塔罗 API",
    description="塔罗牌占卜网站 - 结合AI与经典塔罗文献的智能解读系统",
    version="1.0.0",
)

# WSGI 模式下 lifespan 不会触发，在模块加载时初始化数据库
try:
    init_db()
except Exception as e:
    print(f"[DongDongTarot] DB init warning: {e}")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# 注册 API 路由
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(spreads.router)
app.include_router(readings.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "东东塔罗服务运行正常"}


@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"name": "东东塔罗 API", "version": "1.0.0", "docs": "/docs"}
