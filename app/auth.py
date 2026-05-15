from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.user import User

# bcrypt намеренно медленный — защищает хэши от брутфорса при утечке БД
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _token_from_request(request: Request) -> str | None:
    # Ищем токен сначала в cookie, затем в заголовке Authorization
    token = request.cookies.get("access_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _token_from_request(request)
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_exc

    result = await db.execute(
        select(User)
        .options(selectinload(User.role), selectinload(User.department))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


def require_role(*role_names: str):
    # Фабрика зависимостей: добавить новую роль = одна строка, без дублирования кода
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return current_user
    return dependency


# Готовые зависимости — используются через Depends() в роутерах
get_head = require_role("head_of_department")
get_rop  = require_role("program_director")
