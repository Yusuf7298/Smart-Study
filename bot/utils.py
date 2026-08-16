import logging
from typing import Optional, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

async def safe_reply(
    event: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    parse_mode: Optional[str] = "Markdown"
) -> Optional[Message]:
    """
    Safely sends a reply message to the chat of a Message or CallbackQuery.
    Attempts to use the requested parse_mode (e.g. Markdown).
    If Telegram fails to parse entities, automatically falls back to plain text.
    """
    target = event.message if isinstance(event, CallbackQuery) else event
    if not target:
        return None

    if parse_mode:
        try:
            return await target.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e) or "entity" in str(e).lower():
                logging.warning(f"Markdown parse error, falling back to plain text: {e}")
                return await target.answer(text, parse_mode=None, reply_markup=reply_markup)
            else:
                logging.error(f"TelegramBadRequest in safe_reply: {e}")
                try:
                    return await target.answer(text, parse_mode=None, reply_markup=reply_markup)
                except Exception:
                    return None
        except Exception as e:
            logging.error(f"Error in safe_reply: {e}")
            try:
                return await target.answer(text, parse_mode=None, reply_markup=reply_markup)
            except Exception:
                return None
    else:
        try:
            return await target.answer(text, parse_mode=None, reply_markup=reply_markup)
        except Exception as e:
            logging.error(f"Error in safe_reply plain text: {e}")
            return None

async def safe_edit(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "Markdown"
) -> Optional[Message]:
    """
    Safely edits an existing message.
    Falls back to plain text if Markdown entity parsing fails.
    """
    if parse_mode:
        try:
            return await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup) # type: ignore
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e) or "entity" in str(e).lower():
                logging.warning(f"Markdown parse error in edit, falling back to plain text: {e}")
                return await message.edit_text(text, parse_mode=None, reply_markup=reply_markup) # type: ignore
            elif "message is not modified" in str(e):
                return message
            else:
                logging.error(f"TelegramBadRequest in safe_edit: {e}")
                try:
                    return await message.edit_text(text, parse_mode=None, reply_markup=reply_markup) # type: ignore
                except Exception:
                    return None
        except Exception as e:
            logging.error(f"Error in safe_edit: {e}")
            try:
                return await message.edit_text(text, parse_mode=None, reply_markup=reply_markup) # type: ignore
            except Exception:
                return None
    else:
        try:
            return await message.edit_text(text, parse_mode=None, reply_markup=reply_markup) # type: ignore
        except Exception as e:
            logging.error(f"Error in safe_edit plain text: {e}")
            return None
