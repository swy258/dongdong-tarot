"""牌阵路由"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.spread import Spread

router = APIRouter(prefix="/api/spreads", tags=["牌阵"])


class PositionDef(BaseModel):
    index: int
    name: str
    meaning: str


class CreateSpreadRequest(BaseModel):
    name: str
    description: str | None = None
    positions: list[PositionDef]
    layout_type: str = "grid"
    layout_coords: dict | None = None  # {pos_index: {x, y}} 百分比坐标


@router.get("/")
def get_spreads(
    include_preset: bool = Query(True),
    db: Session = Depends(get_db),
):
    """获取所有牌阵"""
    query = db.query(Spread)
    if include_preset:
        query = query.filter(Spread.is_preset == True)
    else:
        # 获取所有（自定义+预设）
        pass

    spreads = query.order_by(Spread.is_preset.desc(), Spread.created_at.desc()).all()

    return {
        "total": len(spreads),
        "spreads": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "is_preset": s.is_preset,
                "layout_type": s.layout_type or "grid",
                "layout_data": json.loads(s.layout_data) if s.layout_data else None,
                "positions": json.loads(s.positions),
                "position_count": len(json.loads(s.positions)),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in spreads
        ],
    }


@router.get("/presets")
def get_preset_spreads(db: Session = Depends(get_db)):
    """仅获取预设牌阵"""
    spreads = db.query(Spread).filter(Spread.is_preset == True).all()
    return {
        "total": len(spreads),
        "spreads": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "positions": json.loads(s.positions),
                "position_count": len(json.loads(s.positions)),
            }
            for s in spreads
        ],
    }


@router.get("/{spread_id}")
def get_spread(spread_id: int, db: Session = Depends(get_db)):
    """获取单个牌阵详情"""
    spread = db.query(Spread).filter(Spread.id == spread_id).first()
    if not spread:
        raise HTTPException(status_code=404, detail="牌阵不存在")
    return {
        "id": spread.id,
        "name": spread.name,
        "description": spread.description,
        "is_preset": spread.is_preset,
        "positions": json.loads(spread.positions),
        "created_at": spread.created_at.isoformat() if spread.created_at else None,
    }


@router.post("/")
def create_spread(req: CreateSpreadRequest, db: Session = Depends(get_db)):
    """创建自定义牌阵"""
    positions_json = json.dumps(
        [p.model_dump() for p in req.positions], ensure_ascii=False
    )

    spread = Spread(
        name=req.name,
        description=req.description,
        is_preset=False,
        positions=positions_json,
        layout_type=req.layout_type,
        layout_data=json.dumps(req.layout_coords) if req.layout_coords else None,
    )
    db.add(spread)
    db.commit()
    db.refresh(spread)
    return {
        "id": spread.id,
        "name": spread.name,
        "description": spread.description,
        "positions": json.loads(spread.positions),
        "message": "牌阵创建成功",
    }
