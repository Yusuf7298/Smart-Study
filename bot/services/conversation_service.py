import asyncio
from bot.database.repositories import conversation as conv_repo
from bot.database.models import ConversationModel

async def get_history(telegram_id: int, limit: int = 20) -> list[ConversationModel]:
    """Asynchronously retrieves conversation history for a student (cap limited)."""
    return await asyncio.to_thread(conv_repo.get_conversation_history, telegram_id, limit)

async def add_message(telegram_id: int, role: str, message: str) -> None:
    """Asynchronously saves a message to the student's conversation history."""
    await asyncio.to_thread(conv_repo.add_conversation_message, telegram_id, role, message)

async def clear_history(telegram_id: int) -> None:
    """Asynchronously deletes all conversation history for a student."""
    await asyncio.to_thread(conv_repo.delete_conversation_history, telegram_id)
