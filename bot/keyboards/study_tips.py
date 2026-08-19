from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.i18n import t

def get_study_tips_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=t("tips_btn_time", lang), callback_data="tips_cat_time")
        ],
        [
            InlineKeyboardButton(text=t("tips_btn_reading", lang), callback_data="tips_cat_reading")
        ],
        [
            InlineKeyboardButton(text=t("tips_btn_memory", lang), callback_data="tips_cat_memory")
        ],
        [
            InlineKeyboardButton(text=t("tips_btn_digital", lang), callback_data="tips_cat_digital")
        ],
        [
            InlineKeyboardButton(text=t("tips_btn_focus", lang), callback_data="tips_cat_focus")
        ],
        [
            InlineKeyboardButton(text=t("tips_btn_custom", lang), callback_data="tips_cat_custom")
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
