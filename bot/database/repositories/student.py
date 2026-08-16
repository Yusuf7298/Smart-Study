import sqlite3
from typing import Optional
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import StudentModel

def get_student_by_id(telegram_id: int) -> Optional[StudentModel]:
    """Retrieves a student profile from the database by their Telegram ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, first_name, username, grade, education_level, preferred_language, approval_status, created_at, updated_at
        FROM students
        WHERE telegram_id = ?
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    return StudentModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        first_name=row['first_name'],
        username=row['username'],
        grade=row['grade'],
        education_level=row['education_level'],
        preferred_language=row['preferred_language'],
        approval_status=row['approval_status'],
        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
        updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if isinstance(row['updated_at'], str) else row['updated_at']
    )

def create_student(telegram_id: int, first_name: Optional[str], username: Optional[str]) -> StudentModel:
    """Creates a new student profile in the database. Returns the newly created profile."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO students (telegram_id, first_name, username, approval_status)
        VALUES (?, ?, ?, 'APPROVED')
    """, (telegram_id, first_name, username))
    conn.commit()
    conn.close()
    return get_student_by_id(telegram_id)

def register_pending_student(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    grade: int,
    education_level: str,
    preferred_language: str
) -> StudentModel:
    """Registers a student profile in pending status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE telegram_id = ?", (telegram_id,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("""
            UPDATE students
            SET first_name = ?, username = ?, grade = ?, education_level = ?, preferred_language = ?, approval_status = 'PENDING', updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        """, (first_name, username, grade, education_level, preferred_language, telegram_id))
    else:
        cursor.execute("""
            INSERT INTO students (telegram_id, first_name, username, grade, education_level, preferred_language, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
        """, (telegram_id, first_name, username, grade, education_level, preferred_language))
    conn.commit()
    conn.close()
    return get_student_by_id(telegram_id)

def update_approval_status(telegram_id: int, status: str) -> None:
    """Updates the approval status of a student profile (PENDING, APPROVED, REJECTED)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET approval_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (status, telegram_id))
    conn.commit()
    conn.close()

def update_student_profile(
    telegram_id: int, 
    grade: Optional[int] = None, 
    education_level: Optional[str] = None, 
    preferred_language: Optional[str] = None
) -> None:
    """Updates selected fields on a student profile."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if grade is not None:
        updates.append("grade = ?")
        params.append(grade)
    if education_level is not None:
        updates.append("education_level = ?")
        params.append(education_level)
    if preferred_language is not None:
        updates.append("preferred_language = ?")
        params.append(preferred_language)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE students SET {', '.join(updates)} WHERE telegram_id = ?"
        params.append(telegram_id)
        cursor.execute(sql, tuple(params))
        conn.commit()
    conn.close()
