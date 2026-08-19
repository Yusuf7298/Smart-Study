from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.services.i18n import t

def get_main_menu_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
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
            InlineKeyboardButton(text=t("btn_national_exam", lang), callback_data="menu_national_exam")
        ],
        [
            InlineKeyboardButton(text=t("btn_progress", lang), callback_data="menu_progress"),
            InlineKeyboardButton(text=t("btn_profile", lang), callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton(text=t("btn_materials", lang), callback_data="menu_materials"),
            InlineKeyboardButton(text=t("btn_study_tips", lang), callback_data="menu_study_tips")
        ],
        [
            InlineKeyboardButton(text=t("btn_socials", lang), callback_data="menu_socials"),
            InlineKeyboardButton(text=t("btn_language", lang), callback_data="menu_language")
        ],
        [
            InlineKeyboardButton(text=t("btn_help", lang), callback_data="menu_help"),
            InlineKeyboardButton(text=t("btn_support", lang), callback_data="menu_support")
        ],
        [
            InlineKeyboardButton(text=t("btn_feedback", lang), callback_data="menu_feedback")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_reply_keyboard(lang: str = "English") -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="📱 Menu"),
            KeyboardButton(text="🔙 Back"),
            KeyboardButton(text="🧹 Clear")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
