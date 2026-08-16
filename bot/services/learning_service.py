import asyncio
from typing import Optional
from bot.database.repositories import learning as learning_repo
from bot.database.models import LearningSessionModel

async def get_active_session(telegram_id: int) -> Optional[LearningSessionModel]:
    """Asynchronously retrieves the current active learning session for a student."""
    return await asyncio.to_thread(learning_repo.get_active_session_by_id, telegram_id)

async def start_session(telegram_id: int, subject: str, topic: str) -> LearningSessionModel:
    """Asynchronously starts a new learning session, deactivating any existing ones first."""
    # Deactivate existing first
    await asyncio.to_thread(learning_repo.deactivate_all_sessions, telegram_id)
    # Start new
    return await asyncio.to_thread(learning_repo.create_session, telegram_id, subject, topic)

async def deactivate_sessions(telegram_id: int) -> None:
    """Asynchronously stops all active study sessions for a student."""
    await asyncio.to_thread(learning_repo.deactivate_all_sessions, telegram_id)

async def update_stage(session_id: int, stage: str) -> None:
    """Asynchronously updates the learning stage of a session."""
    await asyncio.to_thread(learning_repo.update_session_stage, session_id, stage)
