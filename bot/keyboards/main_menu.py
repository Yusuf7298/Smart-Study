from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.services.i18n import t

def get_main_menu_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    """
    Returns an inline keyboard for the main dashboard featuring all core student actions.
    """
    keyboard = [
        [
            InlineKeyboardButton(text=t("btn_study", lang), callback_data="menu_study"),
            InlineKeyboardButton(text=t("btn_study_pdf", lang), callback_data="menu_study_pdf")
        ],
        [
            InlineKeyboardButton(text=t("btn_quiz", lang), callback_data="menu_quiz"),
            InlineKeyboardButton(text=t("btn_written_test", lang), callback_data="menu_test")
        ],
        [
            InlineKeyboardButton(text=t("btn_short_notes", lang), callback_data="menu_notes"),
            InlineKeyboardButton(text=t("btn_progress", lang), callback_data="menu_progress")
        ],
        [
            InlineKeyboardButton(text=t("btn_materials", lang), callback_data="menu_materials"),
            InlineKeyboardButton(text=t("btn_profile", lang), callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton(text=t("btn_socials", lang), callback_data="menu_socials"),
            InlineKeyboardButton(text=t("btn_language", lang), callback_data="menu_language")
        ],
        [
            InlineKeyboardButton(text=t("btn_help", lang), callback_data="menu_help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_reply_keyboard(lang: str = "English") -> ReplyKeyboardMarkup:
    """
    Returns a persistent bottom reply keyboard with quick access buttons.
    """
    keyboard = [
        [
            KeyboardButton(text=t("btn_study", lang)),
            KeyboardButton(text=t("btn_study_pdf", lang))
        ],
        [
            KeyboardButton(text=t("btn_quiz", lang)),
            KeyboardButton(text=t("btn_written_test", lang)),
            KeyboardButton(text=t("btn_short_notes", lang))
        ],
        [
            KeyboardButton(text=t("btn_materials", lang)),
            KeyboardButton(text=t("btn_progress", lang)),
            KeyboardButton(text=t("btn_profile", lang))
        ],
        [
            KeyboardButton(text=t("btn_socials", lang)),
            KeyboardButton(text=t("btn_help", lang))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
