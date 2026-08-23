import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db").strip()

engine_kwargs = {"echo": False}
if "+asyncpg" in DATABASE_URL:
    # Supabase's connection pooler runs PgBouncer in transaction mode, which is
    # incompatible with asyncpg's server-side prepared statements. Disabling the
    # statement cache and the client-side pool (PgBouncer already pools for us)
    # avoids stale prepared statements when PgBouncer swaps the backend server.
    engine_kwargs["connect_args"] = {"statement_cache_size": 0}
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
