"""Unit tests for the LocalStorageBackend."""

import pytest
import pytest_asyncio

from dataseal.storage import LocalStorageBackend


@pytest_asyncio.fixture
async def storage(tmp_path):
    """Create a LocalStorageBackend with a temp directory."""
    return LocalStorageBackend(base_path=str(tmp_path))


class TestLocalStorageBackend:
    async def test_save_and_load_bytes(self, storage):
        data = b"hello world content"
        await storage.save("test/file.bin", data)
        loaded = await storage.load("test/file.bin")
        assert loaded == data

    async def test_load_nonexistent_raises_file_not_found(self, storage):
        with pytest.raises(FileNotFoundError):
            await storage.load("nonexistent/file.txt")

    async def test_exists_returns_true_after_save(self, storage):
        await storage.save("exists_test.txt", b"data")
        assert await storage.exists("exists_test.txt") is True

    async def test_exists_returns_false_before_save(self, storage):
        assert await storage.exists("not_saved.txt") is False

    async def test_delete_removes_file(self, storage):
        await storage.save("deleteme.txt", b"delete this")
        assert await storage.exists("deleteme.txt") is True
        await storage.delete("deleteme.txt")
        assert await storage.exists("deleteme.txt") is False

    async def test_delete_nonexistent_does_not_raise(self, storage):
        # Should not raise
        await storage.delete("nonexistent/file.txt")

    async def test_get_url_returns_api_path(self, storage):
        url = await storage.get_url("documents/abc/file.pdf")
        assert url.startswith("/api/v1/files/")
        assert "documents/abc/file.pdf" in url

    async def test_save_creates_nested_directories(self, storage, tmp_path):
        await storage.save("a/b/c/deep.txt", b"nested")
        assert (tmp_path / "a" / "b" / "c" / "deep.txt").exists()

    async def test_path_traversal_is_blocked(self, storage):
        with pytest.raises(ValueError, match="path traversal"):
            await storage.save("../../../etc/passwd", b"attack")

    async def test_path_traversal_with_encoded_is_blocked(self, storage):
        with pytest.raises(ValueError, match="path traversal"):
            storage._full_path("../../secret")

    async def test_save_overwrites_existing_file(self, storage):
        await storage.save("overwrite.txt", b"original")
        await storage.save("overwrite.txt", b"updated")
        loaded = await storage.load("overwrite.txt")
        assert loaded == b"updated"

    async def test_save_and_load_binary_pdf_bytes(self, storage):
        # Simulate PDF magic bytes
        pdf_bytes = b"%PDF-1.4 fake pdf content" + b"\x00" * 100
        await storage.save("docs/test.pdf", pdf_bytes)
        loaded = await storage.load("docs/test.pdf")
        assert loaded == pdf_bytes
