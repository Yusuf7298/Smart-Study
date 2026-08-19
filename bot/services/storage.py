
import os
import re
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import config

def sanitize_filename(filename: str) -> str:
    if not filename:
        return "document.pdf"
    clean_base = os.path.basename(filename).replace('\x00', '')
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_base)
    clean = clean.lstrip('.').replace('..', '_')
    return clean or "document.pdf"

class FileStorageProvider(ABC):
    
    @abstractmethod
    async def save(self, telegram_id: int, filename: str, content: bytes, category: str = "uploads") -> Tuple[str, str]:
        pass

    @abstractmethod
    async def get(self, file_path: str) -> Optional[bytes]:
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        pass

class LocalFileStorageProvider(FileStorageProvider):
    def __init__(self, base_upload_dir: str = config.UPLOAD_DIR, base_receipt_dir: str = config.PAYMENT_RECEIPTS_DIR):
        self.base_upload_dir = os.path.abspath(base_upload_dir)
        self.base_receipt_dir = os.path.abspath(base_receipt_dir)
        os.makedirs(self.base_upload_dir, exist_ok=True)
        os.makedirs(self.base_receipt_dir, exist_ok=True)

    def _get_category_dir(self, category: str) -> str:
        if category == "receipts":
            return self.base_receipt_dir
        return self.base_upload_dir

    def _get_user_dir(self, telegram_id: int, category: str = "uploads") -> str:
        cat_dir = self._get_category_dir(category)
        user_dir = os.path.join(cat_dir, str(telegram_id))
        os.makedirs(user_dir, exist_ok=True)
        return os.path.abspath(user_dir)

    def _validate_path_safety(self, file_path: str) -> bool:
        abs_path = os.path.abspath(file_path)
        is_in_uploads = abs_path.startswith(self.base_upload_dir)
        is_in_receipts = abs_path.startswith(self.base_receipt_dir)
        return is_in_uploads or is_in_receipts

    async def save(self, telegram_id: int, filename: str, content: bytes, category: str = "uploads") -> Tuple[str, str]:
        max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValueError(f"File size exceeds maximum allowed limit of {config.MAX_FILE_SIZE_MB}MB")
        safe_name = sanitize_filename(filename)
        user_dir = self._get_user_dir(telegram_id, category)
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        disk_path = os.path.join(user_dir, unique_name)
        if not self._validate_path_safety(disk_path):
            raise PermissionError("Path traversal attempt detected")

        with open(disk_path, "wb") as f:
            f.write(content)
            
        return disk_path, safe_name

    async def get(self, file_path: str) -> Optional[bytes]:
        if not file_path or not self._validate_path_safety(file_path):
            return None
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return None

    async def delete(self, file_path: str) -> bool:
        if not file_path or not self._validate_path_safety(file_path):
            return False
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return False

    async def exists(self, file_path: str) -> bool:
        if not file_path or not self._validate_path_safety(file_path):
            return False
        return os.path.exists(file_path)
    async def save_file(self, telegram_id: int, filename: str, content: bytes) -> Tuple[str, str]:
        return await self.save(telegram_id, filename, content, category="uploads")

    async def read_file(self, file_path: str) -> Optional[bytes]:
        return await self.get(file_path)

    async def delete_file(self, file_path: str) -> bool:
        return await self.delete(file_path)

StorageProvider = FileStorageProvider
LocalStorageProvider = LocalFileStorageProvider
default_storage: FileStorageProvider = LocalFileStorageProvider()
