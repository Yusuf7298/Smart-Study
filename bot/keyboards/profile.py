from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Returns the inline keyboard for the student profile card."""
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
    """Returns a simple inline keyboard with a Cancel button."""
    keyboard = [
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="profile_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
