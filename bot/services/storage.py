"""
Storage abstraction module for Smart Study Bot.
Provides a clean interface (StorageProvider) with LocalStorageProvider implementation,
designed for future S3/cloud storage compatibility.
"""
import os
import re
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import config

def sanitize_filename(filename: str) -> str:
    """Sanitizes user-provided filenames to prevent path traversal and special characters."""
    basename = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
    return clean or "document.pdf"

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, telegram_id: int, filename: str, content: bytes) -> Tuple[str, str]:
        """Saves file bytes. Returns (storage_key_or_path, safe_filename)."""
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> Optional[bytes]:
        """Reads file bytes from storage."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = config.UPLOAD_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_user_dir(self, telegram_id: int) -> str:
        user_dir = os.path.join(self.base_dir, str(telegram_id))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    async def save_file(self, telegram_id: int, filename: str, content: bytes) -> Tuple[str, str]:
        safe_name = sanitize_filename(filename)
        user_dir = self.get_user_dir(telegram_id)
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        disk_path = os.path.join(user_dir, unique_name)
        
        with open(disk_path, "wb") as f:
            f.write(content)
            
        return disk_path, safe_name

    async def read_file(self, file_path: str) -> Optional[bytes]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return False

# Global default storage provider instance
default_storage: StorageProvider = LocalStorageProvider()
