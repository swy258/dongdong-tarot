"""FastAPI 主入口"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base, SessionLocal
from app.config import settings
from app.models import User, Card, Spread, Reading
from app.routers import auth, cards, spreads, readings
from app.services.seed_data import get_card_seed_data, get_preset_spreads


def init_db():
    """初始化数据库：建表 + 种子数据"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 检查是否已初始化
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("[DongDongTarot] Starting up...")
    init_db()
    print("[DongDongTarot] Database initialized.")
    yield
    print("[DongDongTarot] Shutting down...")


app = FastAPI(
    title="东东塔罗 API",
    description="塔罗牌占卜网站 - 结合AI与经典塔罗文献的智能解读系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(spreads.router)
app.include_router(readings.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "东东塔罗服务运行正常"}


# 前端静态文件 - 多路径兜底
_current_dir = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(_current_dir, "static")
# PythonAnywhere 环境下尝试其他路径
for alt in [
    os.path.join(os.path.dirname(_current_dir), "app", "static"),
    os.path.join(os.path.dirname(os.path.dirname(_current_dir)), "backend", "app", "static"),
]:
    if not os.path.exists(STATIC_DIR) and os.path.exists(alt):
        STATIC_DIR = alt

if os.path.exists(STATIC_DIR) and os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

else:
    @app.get("/")
    def root():
        return {
            "name": "东东塔罗 API",
            "version": "1.0.0",
            "docs": "/docs",
        }


# 兜底路由：非 /api/ 的 GET 请求返回 index.html
@app.get("/{path:path}")
async def spa_catchall(path: str):
    import os as _os
    static_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "static")
    if not _os.path.exists(static_dir):
        from fastapi.responses import JSONResponse
        return JSONResponse({"name": "东东塔罗 API", "version": "1.0.0"})
    file_path = _os.path.join(static_dir, path)
    if path and _os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(_os.path.join(static_dir, "index.html"))
