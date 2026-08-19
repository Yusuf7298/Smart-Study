import sqlite3
from typing import Optional
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import LearningSessionModel

def get_active_session_by_id(telegram_id: int) -> Optional[LearningSessionModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, subject, topic, subtopic, stage, is_active, created_at, updated_at
        FROM learning_sessions
        WHERE telegram_id = ? AND is_active = 1
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    return LearningSessionModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        subject=row['subject'],
        topic=row['topic'],
        subtopic=row['subtopic'],
        stage=row['stage'],
        is_active=row['is_active'],
        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
        updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if isinstance(row['updated_at'], str) else row['updated_at']
    )

def deactivate_all_sessions(telegram_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE learning_sessions
        SET is_active = 0, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ? AND is_active = 1
    """, (telegram_id,))
    conn.commit()
    conn.close()

def create_session(telegram_id: int, subject: str, topic: str, stage: str = 'INTRODUCTION') -> LearningSessionModel:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM learning_sessions
        WHERE telegram_id = ? AND subject = ? AND topic = ?
        LIMIT 1
    """, (telegram_id, subject, topic))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE learning_sessions
            SET is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (row['id'],))
    else:
        cursor.execute("""
            INSERT INTO learning_sessions (telegram_id, subject, topic, stage, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (telegram_id, subject, topic, stage))
        
    conn.commit()
    conn.close()
    return get_active_session_by_id(telegram_id)

def update_session_stage(session_id: int, stage: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE learning_sessions
        SET stage = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (stage, session_id))
    conn.commit()
    conn.close()
