from langchain_core.documents import Document

from app.graph.formatting import extract_sources, format_context
from app.retrieval.retriever import RetrievedDocument


def _retrieved(file_path, start_line, end_line, content="code here"):
    return RetrievedDocument(
        document=Document(
            page_content=content,
            metadata={"file_path": file_path, "start_line": start_line, "end_line": end_line},
        ),
        score=0.5,
    )


class TestFormatContext:
    def test_empty_list_produces_empty_string(self):
        assert format_context([]) == ""

    def test_single_document_includes_file_and_lines(self):
        context = format_context([_retrieved("app/auth/service.py", 31, 65, "def foo(): pass")])
        assert "SOURCE 1" in context
        assert "File: app/auth/service.py" in context
        assert "Lines: 31-65" in context
        assert "def foo(): pass" in context

    def test_multiple_documents_are_numbered_in_order(self):
        context = format_context(
            [
                _retrieved("a.py", 1, 2),
                _retrieved("b.py", 3, 4),
            ]
        )
        assert "SOURCE 1" in context
        assert "SOURCE 2" in context
        assert context.index("SOURCE 1") < context.index("SOURCE 2")


class TestExtractSources:
    def test_empty_list(self):
        assert extract_sources([]) == []

    def test_deduplicates_identical_locations(self):
        docs = [_retrieved("a.py", 1, 10), _retrieved("a.py", 1, 10)]
        sources = extract_sources(docs)
        assert len(sources) == 1

    def test_preserves_distinct_locations(self):
        docs = [_retrieved("a.py", 1, 10), _retrieved("a.py", 20, 30)]
        sources = extract_sources(docs)
        assert len(sources) == 2

    def test_source_shape_matches_api_contract(self):
        sources = extract_sources([_retrieved("app/security/jwt.py", 8, 35)])
        assert sources == [{"file_path": "app/security/jwt.py", "start_line": 8, "end_line": 35}]
