from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Change Grade", callback_data="profile_change_grade"),
            InlineKeyboardButton(text="🌍 Change Language", callback_data="profile_change_language")
        ],
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="profile_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="profile_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
