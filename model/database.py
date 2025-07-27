from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle SSL mode for Neon/PostgreSQL
if DATABASE_URL and "sslmode=" in DATABASE_URL:
    # Extract SSL mode from URL and pass it as connection argument
    base_url = DATABASE_URL.split("?")[0]
    ssl_params = DATABASE_URL.split("?")[1] if "?" in DATABASE_URL else ""
    
    # For asyncpg, we need to handle SSL differently
    if "postgresql+asyncpg://" not in base_url:
        if "postgresql://" in base_url:
            base_url = base_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            base_url = "postgresql+asyncpg://" + base_url
    
    # Create engine with SSL configuration and connection pooling
    engine = create_async_engine(
        base_url,
        echo=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "ssl": "require" if "sslmode=require" in ssl_params else None,
            "server_settings": {
                "jit": "off"  # Disable JIT for better compatibility
            },
            "command_timeout": 60,
        }
    )
else:
    # Fallback for local development or different URL formats
    if DATABASE_URL and "postgresql+asyncpg://" not in DATABASE_URL:
        if "postgresql://" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(
        DATABASE_URL, 
        echo=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()