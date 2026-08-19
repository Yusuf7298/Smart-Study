from typing import Dict
from typing import Tuple
import asyncio
import logging
from typing import Optional, List, Any
import config
from bot.database.repositories import student as student_repo
from bot.database.models import StudentModel

def map_grade_to_education_level(grade: str) -> str:
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

async def get_course_price(grade: Optional[str] = None) -> int:
    if grade:
        from bot.database.database import get_grade_price_sync
        custom_price = await asyncio.to_thread(get_grade_price_sync, str(grade))
        if custom_price is not None:
            return custom_price
    try:
        val = await asyncio.to_thread(student_repo.get_system_setting, "price_per_course", str(config.DEFAULT_PRICE_PER_COURSE_ETB))
        return int(val)
    except Exception:
        return config.DEFAULT_PRICE_PER_COURSE_ETB

async def set_course_price(price: int) -> None:
    await asyncio.to_thread(student_repo.set_system_setting, "price_per_course", str(max(0, price)))

async def set_grade_course_price(grade: str, price: int) -> None:
    from bot.database.database import set_grade_price_sync
    await asyncio.to_thread(set_grade_price_sync, str(grade), max(0, price))

async def get_all_grade_prices() -> Dict[str, int]:
    from bot.database.database import get_all_grade_prices_sync
    return await asyncio.to_thread(get_all_grade_prices_sync)

_STUDENT_CACHE: Dict[int, Optional[StudentModel]] = {}

def invalidate_student_cache(telegram_id: int):
    _STUDENT_CACHE.pop(telegram_id, None)

async def get_student(telegram_id: int) -> Optional[StudentModel]:
    if telegram_id in _STUDENT_CACHE:
        return _STUDENT_CACHE[telegram_id]
    student = await asyncio.to_thread(student_repo.get_student_by_id, telegram_id)
    _STUDENT_CACHE[telegram_id] = student
    return student

async def register_student(telegram_id: int, first_name: Optional[str], username: Optional[str]) -> StudentModel:
    invalidate_student_cache(telegram_id)
    return await asyncio.to_thread(student_repo.create_student, telegram_id, first_name, username)

async def register_student_full(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    phone_number: Optional[str],
    grade: str,
    preferred_language: str,
    selected_courses: List[str],
    payment_amount: int,
    approval_status: str = 'PAYMENT_PENDING'
) -> StudentModel:
    invalidate_student_cache(telegram_id)
    edu_level = map_grade_to_education_level(grade)
    res = await asyncio.to_thread(
        student_repo.register_full_student,
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        phone_number=phone_number,
        grade=grade,
        education_level=edu_level,
        preferred_language=preferred_language,
        selected_courses=selected_courses,
        payment_amount=payment_amount,
        approval_status=approval_status
    )
    invalidate_student_cache(telegram_id)
    return res

async def register_student_pending(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    grade: str,
    preferred_language: str
) -> StudentModel:
    price = await get_course_price(grade)
    return await register_student_full(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        phone_number=None,
        grade=grade,
        preferred_language=preferred_language,
        selected_courses=[],
        payment_amount=price,
        approval_status='PAYMENT_PENDING'
    )

async def submit_payment_screenshot(
    telegram_id: int,
    file_id: str,
    file_path: Optional[str] = None
) -> None:
    invalidate_student_cache(telegram_id)
    await asyncio.to_thread(student_repo.update_payment_screenshot, telegram_id, file_id, file_path)

async def approve_student(telegram_id: int) -> None:
    invalidate_student_cache(telegram_id)
    await asyncio.to_thread(student_repo.approve_student, telegram_id)

async def reject_student(telegram_id: int, reason: Optional[str] = None) -> None:
    invalidate_student_cache(telegram_id)
    await asyncio.to_thread(student_repo.reject_student, telegram_id, reason)

async def update_grade(telegram_id: int, grade: str) -> None:
    invalidate_student_cache(telegram_id)
    edu_level = map_grade_to_education_level(grade)
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        grade=grade,
        education_level=edu_level
    )

async def update_language(telegram_id: int, language: str) -> None:
    invalidate_student_cache(telegram_id)
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        preferred_language=language
    )

async def update_courses(telegram_id: int, courses: List[str]) -> None:
    invalidate_student_cache(telegram_id)
    await asyncio.to_thread(student_repo.update_student_courses, telegram_id, courses)
    invalidate_student_cache(telegram_id)

async def update_education_level(telegram_id: int, edu_level: str) -> None:
    await asyncio.to_thread(
        student_repo.update_student_profile, 
        telegram_id, 
        education_level=edu_level
    )

async def update_courses(telegram_id: int, courses: List[str]) -> None:
    await asyncio.to_thread(student_repo.update_student_courses, telegram_id, courses)
    try:
        from bot.database.mongo import get_mongo_db
        import json
        from datetime import datetime
        mongo_db = get_mongo_db()
        if mongo_db:
            await mongo_db.students.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"selected_courses": courses, "selected_courses_json": json.dumps(courses, ensure_ascii=False), "updated_at": datetime.utcnow()}}
            )
    except Exception as me:
        logging.warning(f"MongoDB update courses sync error: {me}")

async def update_approval_status(telegram_id: int, status: str) -> None:
    await asyncio.to_thread(student_repo.update_approval_status, telegram_id, status)

def is_course_registered(student: Optional[StudentModel], course_name: str) -> bool:
    if not student:
        return False
    if not student.selected_courses:
        return True
    
    clean_target = course_name.lower().strip()
    alias_map = {
        "civics": "citizenship education",
        "computer science": "information technology (it)",
        "it": "information technology (it)",
    }
    target_norm = alias_map.get(clean_target, clean_target)

    for c in student.selected_courses:
        clean_c = c.lower().strip()
        c_norm = alias_map.get(clean_c, clean_c)
        if c_norm in target_norm or target_norm in c_norm or ("math" in target_norm and "math" in c_norm):
            return True
    return False

def is_grade_matching(student: Optional[StudentModel], detected_grade: Optional[str]) -> bool:
    if not student or not student.grade or not detected_grade:
        return True
    
    import re
    student_nums = re.findall(r'\d+', str(student.grade))
    detected_nums = re.findall(r'\d+', str(detected_grade))
    
    if student_nums and detected_nums:
        student_val = int(student_nums[0])
        detected_val = int(detected_nums[0])
        
        if student_val == 12:
            return detected_val in [9, 10, 11, 12]
            
        return student_val == detected_val
    return True

def has_national_exam_access(student: Optional[StudentModel]) -> bool:
    if not student:
        return False
    if student.has_exam_package:
        return True
    if student.approval_status == 'APPROVED' and str(student.grade) in ['6', '8', '12']:
        return True
    return False

async def set_exam_package_access(telegram_id: int, has_access: bool = True) -> None:
    await asyncio.to_thread(student_repo.set_exam_package_access, telegram_id, has_access)

def calculate_student_payment(grade: Optional[str], course_count: int, base_price: int) -> Tuple[int, Dict[str, Any]]:
    grade_str = str(grade).strip() if grade else ""
    from bot.database.database import get_grade_price_sync
    custom_price = get_grade_price_sync(grade_str) if grade_str else None
    effective_base_price = custom_price if custom_price is not None else base_price

    is_exam_grade = grade_str in ["6", "8", "12"]
    
    if is_exam_grade:
        review_multiplier = 3 if grade_str == "12" else 1
        review_fee_per_course = int(round(review_multiplier * (effective_base_price * 0.25)))
        per_course_bundle = effective_base_price + review_fee_per_course
        total = max(course_count * per_course_bundle, effective_base_price)
        details = {
            "is_grade_12_package": grade_str == "12",
            "is_exam_package": True,
            "grade_bundle": grade_str,
            "base_price": effective_base_price,
            "review_fee_per_course": review_fee_per_course,
            "per_course_bundle": per_course_bundle,
            "course_count": course_count,
            "total": total
        }
        return total, details
    else:
        total = course_count * effective_base_price
        details = {
            "is_grade_12_package": False,
            "is_exam_package": False,
            "grade_bundle": grade_str,
            "base_price": effective_base_price,
            "review_fee_per_course": 0,
            "per_course_bundle": effective_base_price,
            "course_count": course_count,
            "total": total
        }
        return total, details
