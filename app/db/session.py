from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

Base = declarative_base()

# Connection pooling configuration for better performance
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": 3600,  # Recycle connections after 1 hour
}

# Production optimization: configure connection pool size
if settings.ENVIRONMENT == "production":
    engine_kwargs.update(
        {
            "pool_size": 20,  # Number of persistent connections
            "max_overflow": 40,  # Additional connections when pool is exhausted
            "pool_timeout": 30,  # Seconds to wait for a connection
        }
    )
else:
    # Development settings
    engine_kwargs.update(
        {
            "pool_size": 50,
            "max_overflow": 20,
        }
    )

# Handle SQLite specific args if needed (though we use Postgres in prod)
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    # SQLite doesn't support pool_size/max_overflow with StaticPool, but usually we use QueuePool or NullPool
    # For simplicity in dev with SQLite, we might remove incompatible args if using default pool
    if "pool_size" in engine_kwargs:
        del engine_kwargs["pool_size"]
    if "max_overflow" in engine_kwargs:
        del engine_kwargs["max_overflow"]

# PostgreSQL Engine
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB
mongo_client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
mongo_db = mongo_client.eduecosystem


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
