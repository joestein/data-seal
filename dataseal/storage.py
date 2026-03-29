"""Storage backend abstraction."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles

from dataseal.config import settings


class StorageBackend(ABC):
    """Abstract storage backend for file operations."""

    @abstractmethod
    async def save(self, path: str, data: bytes) -> None:
        ...

    @abstractmethod
    async def load(self, path: str) -> bytes:
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        ...

    @abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        ...


class LocalStorageBackend(StorageBackend):
    """Stores files on local filesystem."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.storage_local_path)
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # May fail outside Docker; directory will be created on first write
            pass

    def _full_path(self, path: str) -> Path:
        # Prevent path traversal
        resolved = (self.base_path / path).resolve()
        if not str(resolved).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid storage path: path traversal detected")
        return resolved

    async def save(self, path: str, data: bytes) -> None:
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

    async def load(self, path: str) -> bytes:
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> None:
        full_path = self._full_path(path)
        if full_path.exists():
            os.remove(full_path)

    async def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        # For local storage, return an API path that the app can serve
        return f"/api/v1/files/{path}"


def get_storage() -> StorageBackend:
    """Get the configured storage backend."""
    if settings.storage_backend == "local":
        return LocalStorageBackend()
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")


# Singleton instance
storage = get_storage()
