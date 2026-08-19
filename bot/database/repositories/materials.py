import sqlite3
from typing import Optional, List
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import StudyMaterialModel

def save_study_material(
    telegram_id: int,
    filename: str,
    file_path: str,
    file_id: Optional[str] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = "application/pdf",
    title: Optional[str] = None,
    page_count: int = 1,
    extracted_text: Optional[str] = None,
    summary: Optional[str] = None,
    topics_json: Optional[str] = None,
    extraction_status: str = "SUCCESS",
    extraction_error: Optional[str] = None,
) -> StudyMaterialModel:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE study_materials
        SET is_active = 0
        WHERE telegram_id = ? AND is_active = 1
    """, (telegram_id,))
    
    cursor.execute("""
        INSERT INTO study_materials (
            telegram_id, filename, file_path, file_id, file_size, mime_type, title,
            page_count, extracted_text, summary, topics_json, extraction_status,
            extraction_error, is_active, is_deleted
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
    """, (
        telegram_id, filename, file_path, file_id, file_size, mime_type,
        title or filename, page_count, extracted_text, summary, topics_json,
        extraction_status, extraction_error
    ))
    material_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_study_material_by_id(material_id)

def get_study_material_by_id(material_id: int) -> Optional[StudyMaterialModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, filename, file_path, file_id, file_size, mime_type, title,
               page_count, extracted_text, summary, topics_json, extraction_status,
               extraction_error, is_active, is_deleted, created_at
        FROM study_materials
        WHERE id = ? AND is_deleted = 0
    """, (material_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_material(row)

def get_active_study_material(telegram_id: int) -> Optional[StudyMaterialModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, filename, file_path, file_id, file_size, mime_type, title,
               page_count, extracted_text, summary, topics_json, extraction_status,
               extraction_error, is_active, is_deleted, created_at
        FROM study_materials
        WHERE telegram_id = ? AND is_active = 1 AND is_deleted = 0
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_material(row)

def get_all_student_materials(telegram_id: int, limit: int = 20) -> List[StudyMaterialModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, filename, file_path, file_id, file_size, mime_type, title,
               page_count, extracted_text, summary, topics_json, extraction_status,
               extraction_error, is_active, is_deleted, created_at
        FROM study_materials
        WHERE telegram_id = ? AND is_deleted = 0
        ORDER BY id DESC
        LIMIT ?
    """, (telegram_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_material(r) for r in rows]

def count_student_materials(telegram_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM study_materials WHERE telegram_id = ? AND is_deleted = 0", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return row['cnt'] if row else 0

def set_active_material(telegram_id: int, material_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE study_materials SET is_active = 0 WHERE telegram_id = ?", (telegram_id,))
    cursor.execute("""
        UPDATE study_materials SET is_active = 1 WHERE id = ? AND telegram_id = ? AND is_deleted = 0
    """, (material_id, telegram_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_study_material(telegram_id: int, material_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE study_materials
        SET is_deleted = 1, is_active = 0
        WHERE id = ? AND telegram_id = ?
    """, (material_id, telegram_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def _row_to_material(row: sqlite3.Row) -> StudyMaterialModel:
    created_at_val = row['created_at']
    if isinstance(created_at_val, str):
        try:
            created_at_val = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
        except ValueError:
            created_at_val = datetime.now()
    keys = row.keys()
    mime_type = row['mime_type'] if 'mime_type' in keys else 'application/pdf'
    extraction_status = row['extraction_status'] if 'extraction_status' in keys else 'SUCCESS'
    extraction_error = row['extraction_error'] if 'extraction_error' in keys else None
    is_deleted = row['is_deleted'] if 'is_deleted' in keys else 0

    return StudyMaterialModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        filename=row['filename'],
        file_path=row['file_path'],
        file_id=row['file_id'],
        file_size=row['file_size'],
        mime_type=mime_type,
        title=row['title'],
        page_count=row['page_count'] or 1,
        extracted_text=row['extracted_text'],
        summary=row['summary'],
        topics_json=row['topics_json'],
        extraction_status=extraction_status,
        extraction_error=extraction_error,
        is_active=row['is_active'],
        is_deleted=is_deleted,
        created_at=created_at_val
    )
