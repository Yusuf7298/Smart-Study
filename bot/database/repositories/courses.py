import json
import sqlite3
from typing import List, Dict, Optional, Any
from bot.database.database import get_db_connection
from bot.database.models import CourseModel, ChapterModel
import config

def get_all_courses() -> List[CourseModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id, name, emoji, description, is_active FROM courses WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        return [
            CourseModel(
                id=r['course_id'],
                name=r['name'],
                emoji=r['emoji'] or "📚",
                description=r['description'],
                is_active=bool(r['is_active'])
            )
            for r in rows
        ]
    
    return [
        CourseModel(
            id=name,
            name=name,
            emoji=info.get("emoji", "📚"),
            description=f"{name} comprehensive curriculum"
        )
        for name, info in config.SUBJECTS.items()
    ]

def get_course_chapters(course_name: str) -> List[ChapterModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT chapter_id, course_id, chapter_number, title, topics_json
        FROM chapters
        WHERE course_id = ? AND is_active = 1
        ORDER BY chapter_number ASC
    """, (course_name,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        result = []
        for r in rows:
            topics = []
            if r['topics_json']:
                try:
                    topics = json.loads(r['topics_json'])
                except Exception:
                    topics = []
            result.append(
                ChapterModel(
                    id=r['chapter_id'],
                    course_id=r['course_id'],
                    chapter_number=r['chapter_number'],
                    title=r['title'],
                    topics=topics
                )
            )
        return result
    sub_info = config.SUBJECTS.get(course_name, {})
    topics_list = sub_info.get("topics", [])
    
    default_chapters = []
    for i in range(1, 7):
        topic_for_chap = topics_list[i-1] if i-1 < len(topics_list) else f"Advanced Concept {i}"
        default_chapters.append(
            ChapterModel(
                id=f"{course_name}_ch{i}",
                course_id=course_name,
                chapter_number=i,
                title=f"Chapter {i}: {topic_for_chap}",
                topics=[topic_for_chap, f"{topic_for_chap} Deep Dive", f"{topic_for_chap} Exam Questions"]
            )
        )
    return default_chapters
