from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# pool_pre_ping=True — перед выдачей соединения из пула проверяется живость PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

# expire_on_commit=False — объекты не протухают после commit, данные доступны без лишних запросов
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    # Контекстный менеджер гарантирует закрытие сессии даже при исключении
    async with AsyncSessionLocal() as session:
        yield session
