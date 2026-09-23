"""sample local repository -> ingestion -> (fake) vector store -> retrieval -> graph.

Uses an in-memory fake in place of QdrantVectorStoreService and a fake LLM
in place of ChatGroq, so this suite never makes a network call - per the
spec, the normal automated test suite must not require a real Groq (or
Qdrant Cloud) request. Live-service verification is done separately.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from app.core.config import get_settings
from app.core.exceptions import BranchNotIndexedError, RepositoryNotFoundError
from app.graph.nodes import INSUFFICIENT_EVIDENCE_ANSWER, RAGNodes
from app.graph.rag_graph import build_rag_graph
from app.ingestion.pipeline import build_documents_for_repository
from app.repositories.identity import build_repository_reference
from app.retrieval.retriever import CodeRetriever
from app.vectorstore.qdrant_store import SearchResult

SAMPLE_REPO = Path(__file__).parent.parent / "fixtures" / "sample_repo"


class FakeVectorStore:
    """In-memory stand-in for QdrantVectorStoreService.similarity_search.

    Applies the same repository_id + branch filter Qdrant would apply, so
    isolation behavior is exercised exactly as it would be in production.
    """

    def __init__(self, documents_by_repo_branch: dict[tuple[str, str], list[Document]]):
        self._data = documents_by_repo_branch

    def similarity_search(self, query_text, *, repository_id, branch, top_k):
        docs = self._data.get((repository_id, branch), [])
        query_terms = [t for t in query_text.lower().split() if t]

        def relevance(doc: Document) -> int:
            text = doc.page_content.lower()
            return sum(text.count(term) for term in query_terms)

        ranked = sorted(docs, key=relevance, reverse=True)
        return [
            SearchResult(content=doc.page_content, metadata=doc.metadata, score=float(relevance(doc)))
            for doc in ranked[:top_k]
        ]


class FakeLLM:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.messages_seen: list = []

    def invoke(self, messages):
        self.messages_seen.append(messages)
        return AIMessage(content=self.response_text)


def _index_sample_repo(repository_id_url: str, branch: str) -> tuple[str, list[Document]]:
    settings = get_settings()
    reference = build_repository_reference("github", repository_id_url, branch)
    documents, _ = build_documents_for_repository(SAMPLE_REPO, reference, settings)
    return reference.repository_id, documents


def test_retriever_returns_content_and_metadata_from_indexed_repo():
    repository_id, documents = _index_sample_repo(
        "https://github.com/example/sample-repo", "main"
    )
    vector_store = FakeVectorStore({(repository_id, "main"): documents})
    retriever = CodeRetriever(vector_store, top_k=8)

    results = retriever.retrieve(
        "create_access_token JWT", repository_id=repository_id, branch="main"
    )

    assert results
    top = results[0]
    assert "create_access_token" in top.document.page_content
    assert top.document.metadata["file_path"] == "app/auth/jwt.py"


def test_repository_isolation_at_the_filter_level():
    repo_a_id, repo_a_docs = _index_sample_repo(
        "https://github.com/example/sample-repo", "main"
    )
    repo_b_id = "github-other-org-other-repo"
    repo_b_docs = [
        Document(
            page_content="def process_payment(order_id): ...",
            metadata={
                "repository_id": repo_b_id,
                "branch": "main",
                "file_path": "app/payments/service.py",
                "file_name": "service.py",
                "language": "python",
                "chunk_index": 0,
                "start_line": 1,
                "end_line": 5,
                "symbol_name": "process_payment",
                "symbol_type": "function",
            },
        )
    ]

    vector_store = FakeVectorStore(
        {(repo_a_id, "main"): repo_a_docs, (repo_b_id, "main"): repo_b_docs}
    )
    retriever = CodeRetriever(vector_store, top_k=8)

    results = retriever.retrieve("payment", repository_id=repo_a_id, branch="main")

    assert all(r.document.metadata["repository_id"] == repo_a_id for r in results)
    assert all("process_payment" not in r.document.page_content for r in results)


def test_full_graph_produces_grounded_answer_with_real_sources():
    repository_id, documents = _index_sample_repo(
        "https://github.com/example/sample-repo", "main"
    )
    vector_store = FakeVectorStore({(repository_id, "main"): documents})
    retriever = CodeRetriever(vector_store, top_k=8)
    llm = FakeLLM("Authentication is handled by authenticate_user in app/auth/service.py.")

    nodes = RAGNodes(
        retriever=retriever,
        llm=llm,
        validate_repository=lambda rid, branch: None,
    )
    graph = build_rag_graph(nodes)

    result = graph.invoke(
        {
            "question": "Where is authentication implemented?",
            "repository_id": repository_id,
            "branch": "main",
        }
    )

    assert "authenticate_user" in result["answer"]
    assert result["sources"]
    assert all("file_path" in source for source in result["sources"])


def test_full_graph_falls_back_when_repository_has_no_indexed_chunks():
    empty_vector_store = FakeVectorStore({})
    retriever = CodeRetriever(empty_vector_store, top_k=8)
    llm = FakeLLM("this text should never be used")

    nodes = RAGNodes(
        retriever=retriever, llm=llm, validate_repository=lambda rid, branch: None
    )
    graph = build_rag_graph(nodes)

    result = graph.invoke(
        {
            "question": "Where is authentication implemented?",
            "repository_id": "some-repo",
            "branch": "main",
        }
    )

    assert result["answer"] == INSUFFICIENT_EVIDENCE_ANSWER
    assert result["sources"] == []


def test_validate_query_propagates_repository_not_found():
    def raise_not_found(repository_id, branch):
        raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")

    nodes = RAGNodes(
        retriever=CodeRetriever(FakeVectorStore({}), top_k=8),
        llm=FakeLLM("unused"),
        validate_repository=raise_not_found,
    )
    graph = build_rag_graph(nodes)

    try:
        graph.invoke({"question": "hi", "repository_id": "missing", "branch": "main"})
        assert False, "expected RepositoryNotFoundError"
    except RepositoryNotFoundError:
        pass


def test_validate_query_propagates_branch_not_indexed():
    def raise_wrong_branch(repository_id, branch):
        raise BranchNotIndexedError("wrong branch")

    nodes = RAGNodes(
        retriever=CodeRetriever(FakeVectorStore({}), top_k=8),
        llm=FakeLLM("unused"),
        validate_repository=raise_wrong_branch,
    )
    graph = build_rag_graph(nodes)

    try:
        graph.invoke({"question": "hi", "repository_id": "repo", "branch": "dev"})
        assert False, "expected BranchNotIndexedError"
    except BranchNotIndexedError:
        pass
