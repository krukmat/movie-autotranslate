from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from .config import get_settings

_settings = get_settings()

if _settings.database_url.startswith("sqlite"):
    async_database_url = _settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    async_database_url = _settings.database_url

engine: AsyncEngine = create_async_engine(async_database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create database schema if missing."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with SessionLocal() as session:
        yield session
