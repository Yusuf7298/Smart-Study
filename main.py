import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
    TelegramNetworkError,
)
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config import BOT_TOKEN, LOCAL_BOT_API_URL, validate_environment
from bot.handlers.start import router as start_router
from bot.handlers.profile import router as profile_router
from bot.handlers.study import router as study_router
from bot.handlers.pdf import router as pdf_router
from bot.handlers.quiz import router as quiz_router
from bot.handlers.registration import router as registration_router
from bot.handlers.admin import router as admin_router
from bot.handlers.actions import router as actions_router
from bot.handlers.progress import router as progress_router
from bot.handlers.materials import router as materials_router
from bot.handlers.study_tips import router as study_tips_router
from bot.handlers.exam import router as exam_router
from bot.handlers.feedback import router as feedback_router
from bot.handlers.freetrial import router as freetrial_router
from bot.handlers.chat import router as chat_router

from bot.middlewares.approval import ApprovalMiddleware
from bot.middlewares.ratelimit import RateLimitMiddleware
from bot.database.database import init_database, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def global_error_handler(event: ErrorEvent) -> bool:
    exception = event.exception
    if isinstance(exception, TelegramForbiddenError):
        logging.warning(f"TelegramForbiddenError: Bot was blocked by user or kicked from chat.")
        return True
    elif isinstance(exception, TelegramRetryAfter):
        logging.warning(f"TelegramRetryAfter: Flooding limit hit. Retry in {exception.retry_after}s.")
        await asyncio.sleep(exception.retry_after)
        return True
    elif isinstance(exception, TelegramBadRequest):
        logging.warning(f"TelegramBadRequest: {exception}")
        return True
    elif isinstance(exception, TelegramNetworkError):
        logging.warning(f"TelegramNetworkError: Network glitch ({exception}). Reconnecting...")
        return True
    elif isinstance(exception, TelegramAPIError):
        logging.error(f"TelegramAPIError: {exception}", exc_info=True)
        return True
    else:
        logging.error(f"Unhandled exception during update processing: {exception}", exc_info=True)
        return True

async def main():
    try:
        validate_environment()
    except ValueError as ve:
        logging.warning(f"Environment validation note: {ve}")
    await init_database()
    session = AiohttpSession(timeout=300)
    if LOCAL_BOT_API_URL:
        server = TelegramAPIServer.from_base(LOCAL_BOT_API_URL, is_local=True)
        session = AiohttpSession(api=server, timeout=300)
        bot = Bot(token=BOT_TOKEN, session=session)  # type: ignore
        logging.info(f"Using Local Telegram Bot API Server at {LOCAL_BOT_API_URL} (enables files up to 2000 MB).")
    else:
        bot = Bot(token=BOT_TOKEN, session=session)  # type: ignore
    dp = Dispatcher()
    dp.error.register(global_error_handler)
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    dp.message.middleware(ApprovalMiddleware())
    dp.callback_query.middleware(ApprovalMiddleware())

    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(admin_router)
    dp.include_router(profile_router)
    dp.include_router(progress_router)
    dp.include_router(study_router)
    dp.include_router(pdf_router)
    dp.include_router(materials_router)
    dp.include_router(quiz_router)
    dp.include_router(exam_router)
    dp.include_router(feedback_router)
    dp.include_router(freetrial_router)
    dp.include_router(actions_router)
    dp.include_router(study_tips_router)
    dp.include_router(chat_router)
    await bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            logging.info("Starting Ethio Smart Study Bot polling...")
            await dp.start_polling(bot, handle_signals=True)
            logging.warning("Aiogram polling cycle ended. Automatically reconnecting in 2s...")
            await asyncio.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            logging.info("Ethio Smart Study Bot stopped gracefully.")
            break
        except Exception as e:
            logging.warning(f"Network / connection blip encountered ({e}). Reconnecting in 3s...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Ethio Smart Study Bot process terminated.")