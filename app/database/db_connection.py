from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL, ASYNC_DATABASE_URL



async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    bind=async_engine
)


Base = declarative_base()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session