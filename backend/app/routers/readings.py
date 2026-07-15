"""占卜记录路由"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reading import Reading
from app.models.spread import Spread
from app.models.card import Card
from app.services.deepseek_service import (
    stream_reading,
    stream_reading_without_rag,
    generate_share_code,
    build_user_message,
    generate_share_summary as gen_share_summary,
)
from app.services.rag_service import rag_service
from app.utils.security import decode_access_token
from app.config import settings

router = APIRouter(prefix="/api/readings", tags=["占卜"])


class DrawnCard(BaseModel):
    position: int
    position_name: str
    card_name: str
    is_reversed: bool = False


class CreateReadingRequest(BaseModel):
    spread_id: int
    question: str
    cards_drawn: list[DrawnCard]


def get_user_id_from_header(authorization: str | None = Header(None)) -> int:
    """从header获取用户ID"""
    if not authorization or not authorization.startswith("Bearer "):
        return 0
    token = authorization[7:]
    payload = decode_access_token(token)
    if not payload:
        return 0
    return int(payload.get("sub", 0))


@router.post("/")
def create_reading(
    req: CreateReadingRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """创建占卜记录并返回解读结果"""
    user_id = get_user_id_from_header(authorization)

    # 获取牌阵
    spread = db.query(Spread).filter(Spread.id == req.spread_id).first()
    if not spread:
        raise HTTPException(status_code=404, detail="牌阵不存在")

    spread_positions = json.loads(spread.positions)

    # 验证牌数
    if len(req.cards_drawn) != len(spread_positions):
        raise HTTPException(
            status_code=400,
            detail=f"牌阵需要{len(spread_positions)}张牌，但你提供了{len(req.cards_drawn)}张",
        )

    # 验证每张牌是否存在
    cards_drawn_data = []
    for card_input in req.cards_drawn:
        card = db.query(Card).filter(Card.name_zh == card_input.card_name).first()
        if not card:
            raise HTTPException(status_code=400, detail=f"卡牌'{card_input.card_name}'不存在")
        cards_drawn_data.append({
            "position": card_input.position,
            "position_name": card_input.position_name,
            "card_name": card_input.card_name,
            "is_reversed": card_input.is_reversed,
        })

    # 创建占卜记录（暂时没有解读全文）
    share_code = generate_share_code()
    reading = Reading(
        user_id=user_id if user_id > 0 else None,
        spread_id=req.spread_id,
        question=req.question,
        cards_drawn=json.dumps(cards_drawn_data, ensure_ascii=False),
        share_code=share_code,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {
        "reading_id": reading.id,
        "share_code": share_code,
        "spread_name": spread.name,
        "cards_drawn": cards_drawn_data,
        "message": "占卜记录已创建，请调用解读接口获取AI解读",
    }


@router.get("/{reading_id}/interpret")
async def interpret_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """返回AI解读（非流式，兼容WSGI）"""
    from fastapi.responses import Response

    user_id = get_user_id_from_header(authorization)
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="占卜记录不存在")

    if reading.user_id and reading.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此占卜记录")

    spread = db.query(Spread).filter(Spread.id == reading.spread_id).first()
    cards_drawn = json.loads(reading.cards_drawn)

    drawn_card_names = [c["card_name"] for c in cards_drawn]
    book_context = rag_service.search(reading.question, drawn_card_names)

    full_text = ""
    try:
        if not settings.DEEPSEEK_API_KEY:
            full_text = "⚠️ DeepSeek API Key 未配置。请在 backend/.env 文件中设置 DEEPSEEK_API_KEY。"
        else:
            async for chunk in stream_reading(
                reading.question,
                spread.name,
                spread.description,
                cards_drawn,
                book_context,
            ):
                full_text += chunk

        # 保存到数据库
        reading.interpretation = full_text
        db.commit()

        # 生成分享摘要
        try:
            summary = await gen_share_summary(
                question=reading.question,
                spread_name=spread.name if spread else "牌阵",
                cards_drawn=cards_drawn,
                full_interpretation=full_text,
            )
            reading.share_summary = summary
            db.commit()
        except Exception as e:
            print(f"Share summary generation failed: {e}")

    except Exception as e:
        full_text = f"解读过程中出现错误：{str(e)}"
        reading.interpretation = full_text
        db.commit()

    return Response(content=full_text, media_type="text/plain; charset=utf-8")


@router.post("/{reading_id}/share-summary")
async def generate_share_summary(
    reading_id: int,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """用AI生成分享卡片的精炼摘要"""
    user_id = get_user_id_from_header(authorization)
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="占卜记录不存在")
    if reading.user_id and reading.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")

    if not reading.interpretation:
        raise HTTPException(status_code=400, detail="还没有解读内容，无法生成摘要")

    spread = db.query(Spread).filter(Spread.id == reading.spread_id).first()
    cards_drawn = json.loads(reading.cards_drawn)

    try:
        summary = await gen_share_summary(
            question=reading.question,
            spread_name=spread.name if spread else "牌阵",
            cards_drawn=cards_drawn,
            full_interpretation=reading.interpretation,
        )
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成分享摘要失败：{str(e)}")


@router.get("/{reading_id}")
def get_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """获取占卜记录详情"""
    user_id = get_user_id_from_header(authorization)
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="占卜记录不存在")

    # 验证权限
    if reading.user_id and reading.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此占卜记录")

    spread = db.query(Spread).filter(Spread.id == reading.spread_id).first()

    return {
        "id": reading.id,
        "question": reading.question,
        "cards_drawn": json.loads(reading.cards_drawn),
        "interpretation": reading.interpretation,
        "share_code": reading.share_code,
        "spread": {
            "id": spread.id,
            "name": spread.name,
            "layout_type": spread.layout_type or "grid",
            "layout_data": json.loads(spread.layout_data) if spread.layout_data else None,
            "positions": json.loads(spread.positions) if spread else [],
        },
        "created_at": reading.created_at.isoformat() if reading.created_at else None,
    }


@router.get("/share/{share_code}")
def get_shared_reading(share_code: str, db: Session = Depends(get_db)):
    """通过分享码获取公开解读（无需登录）"""
    reading = db.query(Reading).filter(Reading.share_code == share_code).first()
    if not reading:
        raise HTTPException(status_code=404, detail="分享链接无效")

    spread = db.query(Spread).filter(Spread.id == reading.spread_id).first()

    return {
        "id": reading.id,
        "question": reading.question,
        "cards_drawn": json.loads(reading.cards_drawn),
        "interpretation": reading.interpretation,
        "share_summary": reading.share_summary,
        "share_code": reading.share_code,
        "spread": {
            "id": spread.id,
            "name": spread.name,
            "layout_type": spread.layout_type or "grid",
            "layout_data": json.loads(spread.layout_data) if spread.layout_data else None,
            "positions": json.loads(spread.positions) if spread else [],
        },
        "created_at": reading.created_at.isoformat() if reading.created_at else None,
    }


@router.get("/")
def get_user_readings(
    skip: int = Query(0),
    limit: int = Query(20),
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """获取用户的历史占卜记录列表"""
    user_id = get_user_id_from_header(authorization)
    if user_id <= 0:
        raise HTTPException(status_code=401, detail="请先登录")

    total = db.query(Reading).filter(Reading.user_id == user_id).count()
    readings = (
        db.query(Reading)
        .filter(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "readings": [
            {
                "id": r.id,
                "question": r.question[:100],
                "cards_drawn": json.loads(r.cards_drawn),
                "share_code": r.share_code,
                "has_interpretation": r.interpretation is not None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ],
    }
