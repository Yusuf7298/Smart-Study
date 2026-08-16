from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUBJECTS

def get_subjects_keyboard() -> InlineKeyboardMarkup:
    """Returns an inline keyboard with all configurable subjects."""
    buttons = []
    # Build buttons in pairs of 2 for a nice grid layout
    row = []
    for sub, info in SUBJECTS.items():
        emoji = info.get("emoji", "📚")
        row.append(InlineKeyboardButton(text=f"{emoji} {sub}", callback_data=f"study_sub_{sub}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    # Append cancel button
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_topics_keyboard(subject: str) -> InlineKeyboardMarkup:
    """Returns an inline keyboard with all topics under the chosen subject."""
    info = SUBJECTS.get(subject, {})
    topics = info.get("topics", [])
    buttons = []
    for topic in topics:
        buttons.append([InlineKeyboardButton(text=topic, callback_data=f"study_topic_{subject}|{topic}")])
        
    # Append navigation buttons: Back to subjects list and Cancel
    buttons.append([
        InlineKeyboardButton(text="🔙 Back", callback_data="study_back_subjects"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
