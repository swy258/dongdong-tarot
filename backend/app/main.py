"""FastAPI 主入口"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.database import engine, Base, SessionLocal
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

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# SPA 中间件：404 时返回静态文件或 index.html（不干扰 API 路由）
@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    # 只处理 GET 请求的 404（跳过 API 路径）
    if response.status_code == 404 and request.method == "GET":
        path = request.url.path.lstrip("/")
        # 先尝试匹配静态文件
        file_path = os.path.join(STATIC_DIR, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # SPA fallback：返回 index.html
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
    return response


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
    """首页 - 返回前端 index.html"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"name": "东东塔罗 API", "version": "1.0.0", "docs": "/docs"}
