import asyncio
from typing import Optional
from bot.database.repositories import learning as learning_repo
from bot.database.repositories import quiz as quiz_repo
from bot.database.models import LearningSessionModel

async def get_active_session(telegram_id: int) -> Optional[LearningSessionModel]:
    return await asyncio.to_thread(learning_repo.get_active_session_by_id, telegram_id)

async def start_session(telegram_id: int, subject: str, topic: str) -> LearningSessionModel:
    await asyncio.to_thread(learning_repo.deactivate_all_sessions, telegram_id)
    await asyncio.to_thread(quiz_repo.deactivate_all_active_quizzes, telegram_id)
    return await asyncio.to_thread(learning_repo.create_session, telegram_id, subject, topic)

async def deactivate_sessions(telegram_id: int) -> None:
    await asyncio.to_thread(learning_repo.deactivate_all_sessions, telegram_id)
    await asyncio.to_thread(quiz_repo.deactivate_all_active_quizzes, telegram_id)

async def update_stage(session_id: int, stage: str) -> None:
    await asyncio.to_thread(learning_repo.update_session_stage, session_id, stage)
