import time
import logging
from collections import defaultdict
from typing import Dict, List
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

import config

class RateLimitMiddleware(BaseMiddleware):
    """
    Sliding window in-memory rate limiting middleware per Telegram user.
    Prevents abuse and quota exhaustion.
    """
    def __init__(self, limit: int = config.RATE_LIMIT_REQUESTS, window: int = config.RATE_LIMIT_WINDOW_SECONDS):
        self.limit = limit
        self.window = window
        self.user_timestamps: Dict[int, List[float]] = defaultdict(list)
        super().__init__()

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        telegram_id = user.id
        
        # Bypass rate limits for administrators
        if telegram_id in config.ADMIN_IDS:
            return await handler(event, data)

        now = time.time()
        timestamps = self.user_timestamps[telegram_id]

        # Purge timestamps older than window
        self.user_timestamps[telegram_id] = [ts for ts in timestamps if now - ts < self.window]

        if len(self.user_timestamps[telegram_id]) >= self.limit:
            logging.warning(f"Rate limit exceeded for user {telegram_id}")
            if isinstance(event, Message):
                await event.answer("⚠️ You are sending requests too quickly. Please wait a few seconds before continuing.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Please slow down! Too many requests.", show_alert=True)
            return

        self.user_timestamps[telegram_id].append(now)
        return await handler(event, data)
