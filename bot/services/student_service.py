import asyncio
from typing import Optional
from bot.database.repositories import student as student_repo
from bot.database.models import StudentModel

def map_grade_to_education_level(grade: str) -> str:
    """Maps a grade string or number to the corresponding standard education level name."""
    try:
        val = int(grade)
        if 1 <= val <= 5:
            return "Elementary School"
        elif 6 <= val <= 8:
            return "Middle School"
        elif 9 <= val <= 12:
            return "High School"
    except ValueError:
        pass
        
    if grade == "College":
        return "College"
    elif grade == "University":
        return "University"
    return "Higher Education"

async def get_student(telegram_id: int) -> Optional[StudentModel]:
    """Asynchronously loads a student's profile from the repository."""
    return await asyncio.to_thread(student_repo.get_student_by_id, telegram_id)

async def register_student(telegram_id: int, first_name: Optional[str], username: Optional[str]) -> StudentModel:
    """Asynchronously registers a new student in the database."""
    return await asyncio.to_thread(student_repo.create_student, telegram_id, first_name, username)

async def update_grade(telegram_id: int, grade: str) -> None:
    """Updates the student's grade and automatically maps/saves their education level."""
    edu_level = map_grade_to_education_level(grade)
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        grade=grade, 
        education_level=edu_level
    )

async def update_language(telegram_id: int, language: str) -> None:
    """Updates the student's preferred language."""
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        preferred_language=language
    )

async def update_education_level(telegram_id: int, edu_level: str) -> None:
    """Updates the student's education level directly (e.g. if set by profile changes)."""
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        education_level=edu_level
    )

async def register_student_pending(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    grade: str,
    preferred_language: str
) -> StudentModel:
    """Asynchronously registers a student in pending status."""
    edu_level = map_grade_to_education_level(grade)
    return await asyncio.to_thread(
        student_repo.register_pending_student,
        telegram_id,
        first_name,
        username,
        grade,
        edu_level,
        preferred_language
    )

async def update_approval_status(telegram_id: int, status: str) -> None:
    """Asynchronously updates the approval status of a student."""
    await asyncio.to_thread(student_repo.update_approval_status, telegram_id, status)
