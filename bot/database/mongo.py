import os
import logging
from typing import Optional, Any, Dict
import config

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False

try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None

_client: Optional[Any] = None
_db: Optional[Any] = None

async def init_mongo_db() -> Optional[Any]:
    global _client, _db
    mongo_uri = getattr(config, "MONGO_URI", "") or os.getenv("MONGO_URI", "") or os.getenv("MONGODB_URI", "")
    
    if not mongo_uri or not MOTOR_AVAILABLE:
        logging.info("MongoDB Atlas URI not configured or motor not available. Operating in local mode.")
        return None

    try:
        db_name = getattr(config, "MONGO_DB_NAME", "ethio_smart_study") or "ethio_smart_study"
        kwargs = {"serverSelectionTimeoutMS": 5000}
        if CA_FILE:
            kwargs["tlsCAFile"] = CA_FILE
        _client = AsyncIOMotorClient(mongo_uri, **kwargs)
        _db = _client[db_name]
        await _db.command("ping")
        logging.info(f"Connected to MongoDB Atlas: {db_name}")
        await _create_indexes(_db)
        return _db
    except Exception as e:
        logging.warning(f"Could not connect to MongoDB Atlas ({e}). Operating with local fallback.")
        _client = None
        _db = None
        return None

async def _create_indexes(db: Any) -> None:
    try:
        await db.students.create_index("telegram_id", unique=True)
        await db.students.create_index("phone")
        await db.students.create_index("registration_status")
        await db.students.create_index("payment_status")
        await db.students.create_index("created_at")
        
        await db.courses.create_index("course_id", unique=True)
        await db.courses.create_index("is_active")
        
        await db.chapters.create_index([("course_id", 1), ("chapter_number", 1)])
        await db.payments.create_index("telegram_id")
        await db.payments.create_index("status")
        await db.payments.create_index("created_at")
        await db.pricing.create_index("is_active")
        await db.pricing.create_index("version")
        await db.learning_sessions.create_index([("telegram_id", 1), ("is_active", 1)])
        await db.quiz_sessions.create_index([("telegram_id", 1), ("status", 1)])
        await db.progress.create_index("telegram_id", unique=True)
        await db.admin_logs.create_index("admin_id")
        await db.admin_logs.create_index("created_at")
        
        logging.info("MongoDB Atlas indexes initialized successfully.")
    except Exception as e:
        logging.warning(f"Error creating MongoDB indexes: {e}")

def get_mongo_db() -> Optional[Any]:
    return _db

async def close_mongo_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logging.info("MongoDB Atlas connection closed.")
