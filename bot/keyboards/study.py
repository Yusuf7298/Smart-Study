from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUBJECTS

def get_subjects_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for sub, info in SUBJECTS.items():
        emoji = info.get("emoji", "📚")
        row.append(InlineKeyboardButton(text=f"{emoji} {sub}", callback_data=f"study_sub_{sub}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_topics_keyboard(subject: str) -> InlineKeyboardMarkup:
    info = SUBJECTS.get(subject, {})
    topics = info.get("topics", [])
    buttons = []
    for topic in topics:
        buttons.append([InlineKeyboardButton(text=topic, callback_data=f"study_topic_{subject}|{topic}")])
    buttons.append([
        InlineKeyboardButton(text="🔙 Back", callback_data="study_back_subjects"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
