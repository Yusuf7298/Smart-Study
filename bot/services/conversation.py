import asyncio
from datetime import datetime
# pyrefly: ignore [missing-import]
from bot.database.db import get_db_connection
from bot.database.models import MessageModel

def _get_history_sync(user_id: int, limit: int) -> list[MessageModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, message, created_at, id, telegram_user_id
        FROM (
            SELECT id, telegram_user_id, role, message, created_at
            FROM messages
            WHERE telegram_user_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
        ORDER BY id ASC
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        created_at_val = row['created_at']
        if isinstance(created_at_val, str):
            try:
                created_at_val = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
            except ValueError:
                created_at_val = datetime.now()
        history.append(
            MessageModel(
                id=row['id'],
                telegram_user_id=row['telegram_user_id'],
                role=row['role'],
                message=row['message'],
                created_at=created_at_val
            )
        )
    return history

async def get_history(user_id: int, limit: int = 20) -> list[MessageModel]:
    return await asyncio.to_thread(_get_history_sync, user_id, limit)

def _add_message_sync(user_id: int, role: str, message: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (telegram_user_id, role, message)
        VALUES (?, ?, ?)
    """, (user_id, role, message))
    conn.commit()
    conn.close()

async def add_message(user_id: int, role: str, message: str) -> None:
    await asyncio.to_thread(_add_message_sync, user_id, role, message)

def _clear_history_sync(user_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM messages WHERE telegram_user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

async def clear_history(user_id: int) -> None:
    await asyncio.to_thread(_clear_history_sync, user_id)
