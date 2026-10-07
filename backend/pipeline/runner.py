import json
import logging
from pipeline.state import GraphState
from pipeline.graph import build_ingest_graph, build_query_graph

logger = logging.getLogger(__name__)


def _empty_state() -> GraphState:
    return {
        "file_path":       "",
        "query":           "",
        "doc_id":          "",
        "all_doc_ids":     [],
        "routed_docs":     [],
        "routing_reason":  "",
        "parsed_text":     "",
        "doc_metadata":    {},
        "chunks":          [],
        "embeddings_done": False,
        "retrieved_docs":  [],
        "filtered_docs":   [],
        "retrieval_score": 0.0,
        "sub_questions":   [],
        "draft_answer":    "",
        "final_answer":    "",
        "answer_quality":  "",
        "retry_count":     0,
        "confidence":      0.0,
        "log":             [],
        "eval_metrics":    {},
    }


def run_ingest(file_path: str) -> dict:
    """Ingest a single PDF — parse, chunk, embed, register."""
    graph   = build_ingest_graph()
    initial = _empty_state()
    initial["file_path"] = file_path
    result  = graph.invoke(initial)
    return {
        "doc_id":          result["doc_id"],
        "total_chunks":    len(result.get("chunks", [])),
        "embeddings_done": result.get("embeddings_done", False),
        "metadata":        result.get("doc_metadata", {}),
        "log":             result.get("log", []),
    }


def run_query(query: str) -> dict:
    """
    Run a full query pipeline.
    doc_id is auto-selected by doc_router_node — no need to pass it.
    """
    graph   = build_query_graph()
    initial = _empty_state()
    initial["query"]           = query
    initial["embeddings_done"] = True

    # self-rag can bounce back to retriever, so cap the graph
    config = {"recursion_limit": 10}

    result = graph.invoke(initial, config=config)

    try:
        payload = json.loads(result.get("final_answer", "{}"))
    except Exception:
        payload = {"answer": result.get("final_answer", ""), "sources": []}

    return {
        "answer":          payload.get("answer", ""),
        "sources":         payload.get("sources", []),
        "confidence":      payload.get("confidence", 0.0),
        "metrics":         payload.get("metrics", {}),
        "docs_searched":   payload.get("docs_searched", []),
        "routing_reason":  payload.get("routing_reason", ""),
        "sub_questions":   result.get("sub_questions", []),
        "retry_count":     result.get("retry_count", 0),
        "retrieval_score": result.get("retrieval_score", 0.0),
        "log":             result.get("log", []),
    }