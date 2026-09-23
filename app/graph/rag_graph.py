"""Compiled LangGraph RAG workflow.

    START
      v
  validate_query -> rewrite_query -> retrieve_code -> check_retrieval
                                                          |        |
                                                 sufficient   insufficient
                                                          v        v
                                                  build_context  fallback_response
                                                          v            |
                                                  generate_answer      |
                                                          v            |
                                                  extract_sources      |
                                                          v            v
                                                         END          END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import RAGNodes
from app.graph.state import RAGState


def build_rag_graph(nodes: RAGNodes):
    graph = StateGraph(RAGState)

    graph.add_node("validate_query", nodes.validate_query)
    graph.add_node("rewrite_query", nodes.rewrite_query)
    graph.add_node("retrieve_code", nodes.retrieve_code)
    graph.add_node("build_context", nodes.build_context)
    graph.add_node("generate_answer", nodes.generate_answer)
    graph.add_node("extract_sources", nodes.extract_sources_node)
    graph.add_node("fallback_response", nodes.fallback_response)

    graph.add_edge(START, "validate_query")
    graph.add_edge("validate_query", "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve_code")
    graph.add_conditional_edges(
        "retrieve_code",
        nodes.check_retrieval,
        {"sufficient": "build_context", "insufficient": "fallback_response"},
    )
    graph.add_edge("build_context", "generate_answer")
    graph.add_edge("generate_answer", "extract_sources")
    graph.add_edge("extract_sources", END)
    graph.add_edge("fallback_response", END)

    return graph.compile()
