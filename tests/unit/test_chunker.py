from app.ingestion.chunker import chunk_file_content

PYTHON_SOURCE = '''"""Module docstring."""


def authenticate_user(username, password):
    """Authenticate a user."""
    return True


class UserService:
    """Handles user lookups."""

    def get_profile(self, user_id):
        return {}
'''


class TestChunkFileContent:
    def test_empty_content_produces_no_chunks(self):
        assert chunk_file_content("   \n  ", "python", 1500, 200) == []

    def test_small_file_produces_one_chunk_with_correct_line_range(self):
        chunks = chunk_file_content(PYTHON_SOURCE, "python", 1500, 200)
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.chunk_index == 0
        assert chunk.start_line == 1
        assert chunk.end_line == len(PYTHON_SOURCE.splitlines())

    def test_symbol_detection_finds_first_function(self):
        chunks = chunk_file_content(PYTHON_SOURCE, "python", 1500, 200)
        assert chunks[0].symbol_name == "authenticate_user"
        assert chunks[0].symbol_type == "function"

    def test_large_file_splits_into_multiple_chunks_with_increasing_lines(self):
        big_source = "\n\n".join(
            f"def function_{i}():\n    return {i}" for i in range(200)
        )
        chunks = chunk_file_content(big_source, "python", 200, 50)
        assert len(chunks) > 1
        for index, chunk in enumerate(chunks):
            assert chunk.chunk_index == index
        # Line ranges should be non-decreasing across chunks.
        for previous, current in zip(chunks, chunks[1:]):
            assert current.start_line >= previous.start_line

    def test_unknown_language_falls_back_without_crashing(self):
        chunks = chunk_file_content("some\nplain\ntext\ncontent\n", "text", 1500, 200)
        assert len(chunks) == 1
        assert chunks[0].symbol_name is None
        assert chunks[0].symbol_type is None
