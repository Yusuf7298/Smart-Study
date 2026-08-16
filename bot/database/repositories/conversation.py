import sqlite3
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import ConversationModel

def get_conversation_history(telegram_id: int, limit: int = 20) -> list[ConversationModel]:
    """Fetches the last `limit` messages for a user in chronological order (ASC)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, role, message, created_at
        FROM (
            SELECT id, telegram_id, role, message, created_at
            FROM conversation
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
        ORDER BY id ASC
    """, (telegram_id, limit))
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
            ConversationModel(
                id=row['id'],
                telegram_id=row['telegram_id'],
                role=row['role'],
                message=row['message'],
                created_at=created_at_val
            )
        )
    return history

def add_conversation_message(telegram_id: int, role: str, message: str) -> None:
    """Inserts a single message into the conversation history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation (telegram_id, role, message)
        VALUES (?, ?, ?)
    """, (telegram_id, role, message))
    conn.commit()
    conn.close()

def delete_conversation_history(telegram_id: int) -> None:
    """Deletes all conversation messages for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM conversation WHERE telegram_id = ?
    """, (telegram_id,))
    conn.commit()
    conn.close()
