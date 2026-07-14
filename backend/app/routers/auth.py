"""用户认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import register_user, authenticate_user, get_user_by_id
from app.utils.security import decode_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str = "塔罗爱好者"


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    from app.services.auth_service import get_user_by_email
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    user = register_user(db, req.email, req.password, req.nickname)
    return {
        "message": "注册成功",
        "user": {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
        },
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    result = authenticate_user(db, req.email, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return result


@router.get("/me")
def get_current_user(token: str = None, db: Session = Depends(get_db)):
    """获取当前用户信息"""
    from fastapi import Header
    # 从Header中获取token
    return {"message": "请使用 /api/auth/me 并携带 Authorization: Bearer <token>"}


def get_current_user_id(authorization: str = None) -> int:
    """从Authorization header中提取用户ID（用于依赖注入）"""
    if not authorization or not authorization.startswith("Bearer "):
        return 0  # 未登录用户
    token = authorization[7:]
    payload = decode_access_token(token)
    if not payload:
        return 0
    return int(payload.get("sub", 0))
