"""认证服务"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token


def register_user(db: Session, email: str, password: str, nickname: str = "塔罗爱好者") -> User:
    """注册新用户"""
    user = User(
        email=email,
        hashed_password=hash_password(password),
        nickname=nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> dict | None:
    """登录认证，返回token和用户信息"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
        },
    }


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()
