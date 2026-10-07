import logging
from services.doc_router_service import doc_router
from pipeline.state import GraphState

logger = logging.getLogger(__name__)


def doc_router_node(state: GraphState) -> dict:
    """
    LangGraph Node: Automatic Document Router
    Reads:  query
    Writes: doc_id, file_path, all_doc_ids, routed_docs, routing_reason, log
    """
    query = state.get("query", "")

    if not query:
        msg = "[doc_router] ERROR: no query provided"
        logger.error(msg)
        return {"doc_id": "", "file_path": "", "log": [msg]}

    logger.info(f"[doc_router] Routing query: '{query[:60]}…'")

    selected = doc_router.select_docs(query, max_docs=2)

    if not selected:
        msg = "[doc_router] No documents found in registry — please upload PDFs first"
        logger.warning(msg)
        return {
            "doc_id":         "",
            "file_path":      "",
            "all_doc_ids":    [],
            "routed_docs":    [],
            "routing_reason": "no documents available",
            "log":            [msg],
        }

    primary    = selected[0]
    all_doc_ids = [d["doc_id"] for d in selected]

    routing_reason = (
        f"Selected '{primary['file_name']}' "
        f"(embedding_score={primary.get('_embedding_score', 'N/A')}) "
        f"from {len(selected)} candidate(s)"
    )

    msg = (
        f"[doc_router] Auto-selected: {[d['file_name'] for d in selected]} "
        f"| primary='{primary['file_name']}'"
    )
    logger.info(msg)

    return {
        "doc_id":         primary["doc_id"],
        "file_path":      primary["file_path"],
        "all_doc_ids":    all_doc_ids,
        "routed_docs":    selected,
        "routing_reason": routing_reason,
        "log":            [msg],
    }