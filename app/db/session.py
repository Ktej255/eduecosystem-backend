from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Global variables for lazy initialization
_engine = None
_SessionLocal = None
_mongo_client = None
_mongo_db = None


def _get_engine_kwargs():
    """Get connection pooling configuration for better performance"""
    engine_kwargs = {
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "connect_args": {
            "connect_timeout": 5  # Timeout in seconds for initial connection
        }
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
        # SQLite doesn't support pool_size/max_overflow
        if "pool_size" in engine_kwargs:
            del engine_kwargs["pool_size"]
        if "max_overflow" in engine_kwargs:
            del engine_kwargs["max_overflow"]

    return engine_kwargs


def get_engine():
    """Lazy initialization of database engine"""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(settings.DATABASE_URL, **_get_engine_kwargs())
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.warning(f"Failed to create database engine: {e}")
            raise
    return _engine


def get_session_local():
    """Lazy initialization of session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_mongo_client():
    """Lazy initialization of MongoDB client"""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
            logger.info("MongoDB client created successfully")
        except Exception as e:
            logger.warning(f"Failed to create MongoDB client: {e}")
            _mongo_client = None
    return _mongo_client


def get_mongo_db():
    """Lazy initialization of MongoDB database"""
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        if client:
            _mongo_db = client.eduecosystem
    return _mongo_db


# Backward compatibility - create class that provides lazy access
class _LazyEngine:
    """Wrapper that provides lazy access to engine"""
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    
    def connect(self):
        return get_engine().connect()
    
    def execute(self, *args, **kwargs):
        return get_engine().execute(*args, **kwargs)


class _LazySessionLocal:
    """Wrapper that provides lazy access to SessionLocal"""
    def __call__(self):
        return get_session_local()()
    
    def __getattr__(self, name):
        return getattr(get_session_local(), name)


# These are accessed by other modules directly
engine = _LazyEngine()
SessionLocal = _LazySessionLocal()


def get_db():
    """Database session dependency for FastAPI"""
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


# For modules that need direct mongo access
def get_mongo():
    """Get MongoDB database instance"""
    return get_mongo_db()


# Lazy mongo properties
class _LazyMongo:
    @property
    def client(self):
        return get_mongo_client()
    
    @property
    def db(self):
        return get_mongo_db()


mongo = _LazyMongo()
mongo_client = property(lambda: get_mongo_client())
mongo_db = property(lambda: get_mongo_db())
