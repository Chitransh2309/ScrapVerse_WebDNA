import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

connect_args = {}
if DATABASE_URL.startswith("postgresql+asyncpg"):
    # Supabase's connection pooler runs PgBouncer in transaction mode, which is
    # incompatible with asyncpg's server-side prepared statements.
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
