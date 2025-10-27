"""
Database connection and session management.
Implements T010 from tasks.md.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create SQLAlchemy sync engine
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create SQLAlchemy async engine (replace postgresql:// with postgresql+asyncpg://)
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


def set_rls_context(session: Session, user_id: str) -> None:
    """
    Set Row-Level Security context variables for current session.
    This enables PostgreSQL RLS policies to filter data by user.

    Args:
        session: SQLAlchemy session
        user_id: User identifier to set in context
    """
    try:
        session.execute(
            f"SET LOCAL app.current_user_id = '{user_id}'"
        )
        logger.debug(f"RLS context set for user: {user_id}")
    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        raise


@event.listens_for(pool.Pool, "connect")
def set_search_path(dbapi_connection: any, connection_record: any) -> None:
    """
    Set PostgreSQL search path on new connections.
    Ensures consistent schema access across the application.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("SET search_path TO public")
    cursor.close()


@event.listens_for(pool.Pool, "checkout")
def receive_checkout(dbapi_connection: any, connection_record: any, connection_proxy: any) -> None:
    """
    Log when a connection is checked out from the pool.
    Useful for monitoring connection usage.
    """
    logger.debug("Connection checked out from pool")


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and cleanup.

    Yields:
        SQLAlchemy session

    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to inject database sessions.

    Yields:
        SQLAlchemy session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database error in request: {e}")
        raise
    finally:
        session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency function for FastAPI to inject async database sessions.

    Yields:
        SQLAlchemy AsyncSession

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database error in request: {e}")
            raise
        finally:
            await session.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should be called on application startup.

    Note: In production, use Alembic migrations instead.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def close_db() -> None:
    """
    Close database connections.
    Should be called on application shutdown.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def close_async_db() -> None:
    """
    Close async database connections.
    Should be called on application shutdown.
    """
    try:
        await async_engine.dispose()
        logger.info("Async database connections closed")
    except Exception as e:
        logger.error(f"Error closing async database: {e}")


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False


__all__ = [
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "get_async_db",
    "get_db_context",
    "set_rls_context",
    "init_db",
    "close_db",
    "close_async_db",
    "check_db_connection",
]
