import logging
import json
from datetime import datetime, timezone
from pipeline.state import GraphState
from utils.json_sanitize import json_safe

logger = logging.getLogger(__name__)


def answer_node(state: GraphState) -> dict:
    """
    LangGraph Node: Final Answer
    Reads:  draft_answer, eval_metrics, filtered_docs,
            confidence, routed_docs, routing_reason
    Writes: final_answer, log
    """
    draft          = state.get("draft_answer", "")
    metrics        = state.get("eval_metrics", {})
    confidence     = state.get("confidence", 0.0)
    docs           = state.get("filtered_docs", [])
    routed_docs    = state.get("routed_docs", [])
    routing_reason = state.get("routing_reason", "")

    final   = draft or "I was unable to find sufficient information to answer your question."
    sources = _build_sources(docs)

    doc_attribution = [
        {
            "doc_id":    d.get("doc_id", ""),
            "file_name": d.get("file_name", ""),
            "pages":     d.get("total_pages", "?"),
        }
        for d in routed_docs
    ]

    response = {
        "answer":          final,
        "sources":         sources,
        "confidence":      round(confidence, 3),
        "metrics":         metrics,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "docs_searched":   doc_attribution,
        "routing_reason":  routing_reason,
    }

    msg = (
        f"[answer] Final answer ready — "
        f"confidence={confidence:.2f}, "
        f"sources={len(sources)}, "
        f"docs_searched={len(doc_attribution)}, "
        f"chars={len(final)}"
    )
    logger.info(msg)
    return {"final_answer": json.dumps(json_safe(response)), "log": [msg]}


def _build_sources(docs: list) -> list:
    seen    = set()
    sources = []
    for doc in docs:
        key = (
            doc.metadata.get("section", ""),
            doc.metadata.get("page_number", ""),
            doc.metadata.get("source_doc_id", ""),
        )
        if key not in seen:
            seen.add(key)
            sources.append({
                "section":        doc.metadata.get("section", "unknown"),
                "page":           doc.metadata.get("page_number"),
                "crag_score":     doc.metadata.get("crag_score"),
                "source_doc_id":  doc.metadata.get("source_doc_id", ""),
                "snippet":        doc.page_content[:120] + "…",
            })
    return sources
