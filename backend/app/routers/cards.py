"""78张塔罗牌路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.card import Card

router = APIRouter(prefix="/api/cards", tags=["卡牌"])


@router.get("/")
def get_all_cards(
    card_type: str | None = Query(None, description="筛选类型: major/minor"),
    suit: str | None = Query(None, description="筛选牌组: 权杖/圣杯/宝剑/星币"),
    search: str | None = Query(None, description="搜索牌名"),
    db: Session = Depends(get_db),
):
    """获取78张塔罗牌列表"""
    query = db.query(Card)

    if card_type:
        query = query.filter(Card.card_type == card_type)
    if suit:
        query = query.filter(Card.suit == suit)
    if search:
        query = query.filter(
            Card.name_zh.contains(search) | Card.name_en.contains(search)
        )

    cards = query.order_by(Card.card_type.desc(), Card.suit, Card.number).all()

    return {
        "total": len(cards),
        "cards": [
            {
                "id": c.id,
                "name_zh": c.name_zh,
                "name_en": c.name_en,
                "card_type": c.card_type,
                "suit": c.suit,
                "number": c.number,
                "keywords": c.keywords,
                "description": c.description,
            }
            for c in cards
        ],
    }


@router.get("/{card_id}")
def get_card(card_id: int, db: Session = Depends(get_db)):
    """获取单张牌详情"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return {
        "id": card.id,
        "name_zh": card.name_zh,
        "name_en": card.name_en,
        "card_type": card.card_type,
        "suit": card.suit,
        "number": card.number,
        "keywords": card.keywords,
        "description": card.description,
    }
