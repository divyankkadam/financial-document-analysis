import logging
from services.retriever_service import RetrieverService
from pipeline.state import GraphState

logger     = logging.getLogger(__name__)
_retriever = RetrieverService()


def retriever_node(state: GraphState) -> dict:
    query       = state.get("query", "")
    doc_id      = state.get("doc_id", "")
    all_doc_ids = state.get("all_doc_ids", [])
    retry       = state.get("retry_count", 0)

    if not query or not doc_id:
        msg = "[retriever] ERROR: missing query or doc_id"
        return {"retrieved_docs": [], "retrieval_score": 0.0, "log": [msg]}

    target_docs     = all_doc_ids if all_doc_ids else [doc_id]
    score_threshold = 0.0    # always 0.0 for local embeddings
    k_per_doc       = 6

    all_results = []

    for did in target_docs:
        try:
            results = _retriever.retrieve(
                doc_id=did,
                query=query,
                k=k_per_doc,
                expand_queries=False,   # disable expansion (LLM may fail)
                score_threshold=score_threshold,
            )
            for doc, score in results:
                doc.metadata["source_doc_id"] = did
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"[retriever] Failed for doc {did[:8]}: {e}")

    if not all_results:
        msg = f"[retriever] No results for query='{query[:50]}'"
        logger.warning(msg)
        return {"retrieved_docs": [], "retrieval_score": 0.0, "log": [msg]}

    all_results.sort(key=lambda x: x[1])  # L2 distance: lower = better
    final  = all_results[:k_per_doc]
    docs   = [doc for doc, _ in final]
    scores = [1.0 / (1.0 + score) for _, score in final]
    avg    = round(sum(scores) / len(scores), 3)

    for doc, score in final:
        doc.metadata["retrieval_score"] = round(1.0 / (1.0 + score), 4)

    msg = f"[retriever] Retrieved {len(docs)} chunks, avg_score={avg:.3f}"
    logger.info(msg)
    return {"retrieved_docs": docs, "retrieval_score": avg, "log": [msg]}