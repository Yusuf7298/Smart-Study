import uuid
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import config
from bot.database.database import get_db_connection
from bot.database.models import PricingModel
from bot.database.mongo import get_mongo_db

def get_active_course_price() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = 'price_per_course'")
    row = cursor.fetchone()
    conn.close()
    if row and row['value']:
        try:
            return int(row['value'])
        except ValueError:
            return config.DEFAULT_PRICE_PER_COURSE_ETB
    return config.DEFAULT_PRICE_PER_COURSE_ETB

async def get_active_course_price_async() -> int:
    db = get_mongo_db()
    if db is not None:
        try:
            doc = await db.pricing.find_one({"is_active": True}, sort=[("version", -1)])
            if doc and "course_price" in doc:
                return int(doc["course_price"])
        except Exception:
            pass
    return get_active_course_price()

def set_course_price(new_price: int, admin_id: Optional[int] = None) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES ('price_per_course', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, (str(new_price),))
    pricing_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO pricing (pricing_id, course_price, currency, is_active, version, created_at)
        VALUES (?, ?, 'ETB', 1, (SELECT COALESCE(MAX(version), 0) + 1 FROM pricing), CURRENT_TIMESTAMP)
    """, (pricing_id, new_price))
    
    conn.commit()
    conn.close()

async def set_course_price_async(new_price: int, admin_id: Optional[int] = None) -> None:
    set_course_price(new_price, admin_id)
    db = get_mongo_db()
    if db is not None:
        try:
            await db.pricing.update_many({}, {"$set": {"is_active": False}})
            await db.pricing.insert_one({
                "pricing_id": str(uuid.uuid4()),
                "course_price": new_price,
                "currency": "ETB",
                "is_active": True,
                "created_by": admin_id,
                "created_at": datetime.utcnow()
            })
        except Exception:
            pass
