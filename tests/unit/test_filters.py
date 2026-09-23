from pathlib import Path

from app.ingestion.filters import is_indexable_file


def _write(tmp_path: Path, name: str, content: str = "print('hi')\n") -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


class TestIsIndexableFile:
    def test_supported_extension_is_indexable(self, tmp_path):
        path = _write(tmp_path, "service.py")
        assert is_indexable_file(path, max_file_size_kb=512) is True

    def test_always_index_filename(self, tmp_path):
        path = _write(tmp_path, "Dockerfile", "FROM python:3.12\n")
        assert is_indexable_file(path, max_file_size_kb=512) is True

    def test_unsupported_extension_is_skipped(self, tmp_path):
        path = _write(tmp_path, "notes.pdf", "not really a pdf")
        assert is_indexable_file(path, max_file_size_kb=512) is False

    def test_ignored_suffix_is_skipped(self, tmp_path):
        path = _write(tmp_path, "bundle.min.js", "var x=1;")
        assert is_indexable_file(path, max_file_size_kb=512) is False

    def test_lock_file_is_skipped(self, tmp_path):
        path = _write(tmp_path, "package.lock", "{}")
        assert is_indexable_file(path, max_file_size_kb=512) is False

    def test_oversized_file_is_skipped(self, tmp_path):
        path = _write(tmp_path, "big.py", "x = 1\n" * 100_000)
        assert is_indexable_file(path, max_file_size_kb=1) is False

    def test_binary_file_is_skipped_even_with_supported_extension(self, tmp_path):
        path = tmp_path / "fake.py"
        path.write_bytes(b"\x00\x01\x02binary-not-source")
        assert is_indexable_file(path, max_file_size_kb=512) is False

    def test_missing_file_is_skipped(self, tmp_path):
        path = tmp_path / "gone.py"
        assert is_indexable_file(path, max_file_size_kb=512) is False
