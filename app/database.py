import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import AsyncGenerator
from .models import Base  
from app.config import DATABASE_URL


ASYNC_DATABASE_URL = DATABASE_URL

engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    echo=True,
    future=True,
    connect_args={"check_same_thread": False} 
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False 
)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("База данных и таблицы успешно инициализированы.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()