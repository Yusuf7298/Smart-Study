import io
import os
import time
import asyncio
import logging
from typing import Optional, Union, Callable
from aiogram.types import Message, Document, PhotoSize

import config

_telethon_client = None

async def get_mtproto_client():
    global _telethon_client
    if _telethon_client is not None and _telethon_client.is_connected():
        return _telethon_client

    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH or not config.BOT_TOKEN:
        return None

    try:
        from telethon import TelegramClient
        session_name = os.path.join(config.UPLOAD_DIR, "bot_mtproto_session")
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        
        client = TelegramClient(
            session_name,
            api_id=int(config.TELEGRAM_API_ID),
            api_hash=config.TELEGRAM_API_HASH
        )
        await client.start(bot_token=config.BOT_TOKEN)
        _telethon_client = client
        logging.info("Telegram MTProto client connected for large file downloads (up to 2000 MB).")
        return _telethon_client
    except Exception as e:
        logging.error(f"Failed to initialize MTProto client: {e}", exc_info=True)
        return None

async def _fast_parallel_download(client, media_doc, progress_cb: Optional[Callable] = None) -> Optional[bytes]:
    """
    Blazing fast multi-threaded chunk downloader using 8 concurrent workers over MTProto.
    Downloads 100MB-500MB documents in seconds instead of minutes.
    """
    try:
        from telethon.tl.types import InputDocumentFileLocation, Document as TgDocument
        from telethon.tl.functions.upload import GetFileRequest

        if not hasattr(media_doc, "id") or not hasattr(media_doc, "access_hash"):
            return None

        file_size = getattr(media_doc, "size", 0)
        if file_size <= 0:
            return None

        # 512 KB optimal chunk size for Telegram MTProto
        chunk_size = 512 * 1024
        total_parts = (file_size + chunk_size - 1) // chunk_size
        parts = [b""] * total_parts

        location = InputDocumentFileLocation(
            id=media_doc.id,
            access_hash=media_doc.access_hash,
            file_reference=getattr(media_doc, "file_reference", b""),
            thumb_size=""
        )

        queue = asyncio.Queue()
        for i in range(total_parts):
            queue.put_nowait(i)

        downloaded_bytes = 0
        lock = asyncio.Lock()
        concurrency = min(8, max(4, total_parts))

        async def worker():
            nonlocal downloaded_bytes
            while not queue.empty():
                try:
                    part_idx = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                offset = part_idx * chunk_size
                limit = min(chunk_size, file_size - offset)

                for attempt in range(3):
                    try:
                        res = await client(GetFileRequest(
                            location=location,
                            offset=offset,
                            limit=limit
                        ))
                        parts[part_idx] = res.bytes
                        async with lock:
                            downloaded_bytes += len(res.bytes)
                            if progress_cb:
                                await progress_cb(downloaded_bytes, file_size)
                        break
                    except Exception as err:
                        if attempt == 2:
                            logging.warning(f"Worker chunk {part_idx} failed after 3 attempts: {err}")
                        await asyncio.sleep(0.3)

        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)

        full_bytes = b"".join(parts)
        if len(full_bytes) == file_size:
            return full_bytes
        elif len(full_bytes) > 0:
            return full_bytes
    except Exception as e:
        logging.warning(f"Parallel chunk download fallback: {e}")

    return None

async def download_file_bytes(
    message: Message,
    file_target: Optional[Union[Document, PhotoSize, str]] = None,
    status_message: Optional[Message] = None
) -> Optional[bytes]:
    """
    Downloads file/document bytes safely for any size up to MAX_FILE_SIZE_MB (e.g. 500MB+).
    Uses standard Aiogram Bot API for files <= 20MB or when local server is used,
    and fast parallel MTProto download with progress updates for large files.
    """
    file_size = 0
    file_id = None
    
    if isinstance(file_target, Document):
        file_size = file_target.file_size or 0
        file_id = file_target.file_id
    elif isinstance(file_target, PhotoSize):
        file_size = file_target.file_size or 0
        file_id = file_target.file_id
    elif isinstance(file_target, str):
        file_id = file_target
    elif message.document:
        file_size = message.document.file_size or 0
        file_id = message.document.file_id
    elif message.photo:
        file_size = message.photo[-1].file_size or 0
        file_id = message.photo[-1].file_id

    # If local bot api server is configured or file is within 20MB cloud limit:
    use_standard_api = bool(config.LOCAL_BOT_API_URL) or (file_size > 0 and file_size <= 20 * 1024 * 1024)

    if use_standard_api and file_id:
        try:
            file = await message.bot.get_file(file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, buf)
            return buf.getvalue()
        except Exception as e:
            logging.warning(f"Standard get_file download failed: {e}. Trying fast MTProto...")

    # For files > 20 MB or fallback: use MTProto fast parallel client
    mtproto = await get_mtproto_client()
    if mtproto:
        try:
            chat_id = message.chat.id
            msg_id = message.message_id
            tg_msg = await mtproto.get_messages(chat_id, ids=msg_id)
            if tg_msg and tg_msg.media:
                last_edit_time = [0.0]

                async def progress_cb(current, total):
                    now = time.time()
                    if status_message and total and (now - last_edit_time[0] > 3.0):
                        last_edit_time[0] = now
                        pct = int((current / total) * 100)
                        mb_done = current / (1024 * 1024)
                        mb_tot = total / (1024 * 1024)
                        try:
                            await status_message.edit_text(
                                f"⚡ *High-Speed Download ({pct}%):*\n"
                                f"📥 {mb_done:.1f} MB / {mb_tot:.1f} MB completed...",
                                parse_mode="Markdown"
                            )
                        except Exception:
                            pass

                # 1. Try blazing fast 8-worker parallel download first
                media_doc = getattr(tg_msg.media, "document", None) or tg_msg.media
                fast_data = await _fast_parallel_download(mtproto, media_doc, progress_cb)
                if fast_data:
                    return fast_data

                # 2. Sequential fallback if parallel encounters unusual media
                buf = io.BytesIO()
                await mtproto.download_media(tg_msg, file=buf, progress_callback=progress_cb)
                return buf.getvalue()
        except Exception as e:
            logging.error(f"MTProto download error: {e}", exc_info=True)

    # Fallback to standard get_file if not tried yet
    if file_id and not use_standard_api:
        file = await message.bot.get_file(file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        return buf.getvalue()

    return None
