"""
Database session management with FULLY lazy initialization.
The database connection is ONLY attempted when a request actually needs it.
This allows the app to start even if the database is unreachable.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Base is always available - it doesn't require a connection
Base = declarative_base()

# Global variables - all start as None
_engine = None
_SessionLocal = None
_mongo_client = None
_mongo_db = None


def _get_engine_kwargs():
    """Get connection pooling configuration"""
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "connect_args": {
            "connect_timeout": 10  # Increased timeout
        }
    }

    if settings.ENVIRONMENT == "production":
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        })
    else:
        engine_kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
        })

    if "sqlite" in settings.DATABASE_URL:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)

    return engine_kwargs


def get_engine():
    """Get or create the database engine. May raise if DB is unreachable."""
    global _engine
    if _engine is None:
        logger.info(f"Creating database engine for: {settings.DATABASE_URL[:50]}...")
        _engine = create_engine(settings.DATABASE_URL, **_get_engine_kwargs())
        logger.info("Database engine created")
    return _engine


def get_session_local():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Backward compatibility: SessionLocal() creates a session
class _SessionLocalFactory:
    """Callable factory that acts like the old SessionLocal"""
    def __call__(self):
        return get_session_local()()
    
    def __getattr__(self, name):
        return getattr(get_session_local(), name)


SessionLocal = _SessionLocalFactory()


# Backward compatibility: engine attribute access
class _EngineProxy:
    """Proxy for lazy engine access"""
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    
    def connect(self):
        return get_engine().connect()
    
    def execute(self, *args, **kwargs):
        return get_engine().execute(*args, **kwargs)
    
    def begin(self):
        return get_engine().begin()
    
    def __repr__(self):
        return f"<EngineProxy for {settings.DATABASE_URL[:30]}...>"


engine = _EngineProxy()


def get_db():
    """FastAPI dependency for database sessions."""
    db = None
    try:
        db = get_session_local()()
        yield db
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    finally:
        if db is not None:
            db.close()


# MongoDB (also lazy)
def get_mongo_client():
    """Get or create MongoDB client."""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = AsyncIOMotorClient(
                settings.MONGO_URL, 
                serverSelectionTimeoutMS=5000
            )
        except Exception as e:
            logger.warning(f"MongoDB client creation failed: {e}")
    return _mongo_client


def get_mongo_db():
    """Get MongoDB database."""
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        if client:
            _mongo_db = client.eduecosystem
    return _mongo_db


# Legacy aliases
mongo_client = None  # Access through get_mongo_client()
mongo_db = None  # Access through get_mongo_db()

def get_mongo():
    """Get MongoDB database instance."""
    return get_mongo_db()
