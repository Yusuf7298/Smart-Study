import re
import html
import logging
from typing import Optional, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

# Map common math superscripts and subscripts to unicode
SUPERSCRIPTS = {
    "^0": "⁰", "^1": "¹", "^2": "²", "^3": "³", "^4": "⁴",
    "^5": "⁵", "^6": "⁶", "^7": "⁷", "^8": "⁸", "^9": "⁹",
    "^n": "ⁿ", "^x": "ˣ", "^y": "ʸ", "^+": "⁺", "^-": "⁻"
}
SUBSCRIPTS = {
    "_0": "₀", "_1": "₁", "_2": "₂", "_3": "₃", "_4": "₄",
    "_5": "₅", "_6": "₆", "_7": "₇", "_8": "₈", "_9": "₉",
    "_n": "ₙ", "_x": "ₓ", "_y": "ᵧ", "_i": "ᵢ", "_j": "ⱼ"
}

def strip_all_formatting(text: str) -> str:
    """Strips all HTML tags, asterisks, hashtags, and markdown symbols for clean fallback text."""
    if not text:
        return ""
    # Remove HTML tags
    t = re.sub(r"<[^>]+>", "", text)
    # Remove asterisks and hashtags
    t = t.replace("*", "").replace("#", "")
    return t.strip()

def markdown_to_telegram_html(text: str) -> str:
    """
    Converts Markdown / raw text into clean, safe Telegram HTML:
    - Converts *bold* or **bold** into <b>bold</b>.
    - Converts _italic_ into <i>italic</i>.
    - Converts `code` into <code>code</code>.
    - Converts [label](url) into <a href="url">label</a>.
    - Converts ### Heading into <b>Heading</b>.
    - Converts bullet items (* item, - item) into clean unicode bullets (• item).
    - Converts math powers ($r^3$, $x^2$) into clean unicode math (r³, x²).
    - Converts dividers (---, ___) into clean dividers (━━━━━━━━━━━━━━━━━━━━).
    - Eliminates any raw '#' or '*' artifacts.
    """
    if not text:
        return ""

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # 1. Dividers
        if stripped in ["---", "___", "***", "----", "____", "*****"]:
            cleaned_lines.append("━━━━━━━━━━━━━━━━━━━━")
            continue

        # 2. Markdown headers (### Heading, #### Heading, etc.) -> <b>Heading</b>
        if re.match(r"^#{1,6}\s+", stripped):
            header_text = re.sub(r"^#{1,6}\s+", "", stripped).strip()
            # Clean inner markdown
            header_text = header_text.replace("**", "").replace("*", "")
            cleaned_lines.append(f"<b>{html.escape(header_text)}</b>")
            continue

        # 3. Bullet points (* item, - item, * **Term:**) -> • <b>Term:</b>
        if re.match(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", lambda m: f"• <b>{html.escape(m.group(1))}</b>", line)
        elif re.match(r"^\s*[\*\-]\s+\*(.*?)\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*(.*?)\*", lambda m: f"• <b>{html.escape(m.group(1))}</b>", line)
        elif re.match(r"^\s*[\*\-]\s+", line):
            line = re.sub(r"^\s*[\*\-]\s+", "• ", line)

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)

    # 4. Convert superscripts & subscripts in math formulas
    for k, v in SUPERSCRIPTS.items():
        result = result.replace(k, v)
    for k, v in SUBSCRIPTS.items():
        result = result.replace(k, v)

    # 5. Clean LaTeX math delimiters ($formula$ -> formula)
    result = re.sub(r"\$\$([^\$\n]+)\$\$", r"\1", result)
    result = re.sub(r"\$([^\$\n]+)\$", r"\1", result)

    # 6. Convert inline markdown hyperlinks [label](url) -> <a href="url">label</a>
    result = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s\)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>',
        result
    )

    # 7. Convert inline code `text` -> <code>text</code>
    result = re.sub(r"`([^`\n]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", result)

    # 8. Convert bold **text** or *text* -> <b>text</b>
    result = re.sub(r"\*\*\*([^\*\n]+)\*\*\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)
    result = re.sub(r"\*\*([^\*\n]+)\*\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)
    result = re.sub(r"\*([^\*\n]+)\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)

    # 9. Convert italics _text_ -> <i>text</i>
    result = re.sub(r"_([^_	\n]+)_", lambda m: f"<i>{html.escape(m.group(1))}</i>", result)

    # 10. Strip any remaining rogue asterisks (*) or hashtags (#)
    result = result.replace("*", "").replace("#", "")

    # 11. Collapse excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()

def clean_telegram_text(text: str) -> str:
    """Wrapper that converts text to safe Telegram HTML formatting."""
    return markdown_to_telegram_html(text)

async def safe_reply(
    event: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    parse_mode: Optional[str] = "HTML"
) -> Optional[Message]:
    """
    Safely sends a reply message formatted with Telegram HTML bold/italic/code tags.
    If Telegram fails to parse HTML entities, automatically falls back to clean plain text.
    """
    target = event.message if isinstance(event, CallbackQuery) else event
    if not target:
        return None

    html_text = markdown_to_telegram_html(text)

    try:
        return await target.answer(html_text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        logging.warning(f"HTML parse error in safe_reply, falling back to plain text: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await target.answer(plain, parse_mode=None, reply_markup=reply_markup)
        except Exception:
            return None
    except Exception as e:
        logging.error(f"Error in safe_reply: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await target.answer(plain, parse_mode=None, reply_markup=reply_markup)
        except Exception:
            return None

async def safe_edit(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML"
) -> Optional[Message]:
    """
    Safely edits an existing message with Telegram HTML formatting.
    Falls back to clean plain text if HTML parsing fails.
    """
    html_text = markdown_to_telegram_html(text)

    try:
        return await message.edit_text(html_text, parse_mode="HTML", reply_markup=reply_markup) # type: ignore
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return message
        logging.warning(f"HTML parse error in safe_edit, falling back to plain text: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await message.edit_text(plain, parse_mode=None, reply_markup=reply_markup) # type: ignore
        except Exception:
            return None
    except Exception as e:
        logging.error(f"Error in safe_edit: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await message.edit_text(plain, parse_mode=None, reply_markup=reply_markup) # type: ignore
        except Exception:
            return None
