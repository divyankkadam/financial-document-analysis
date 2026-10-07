import logging
from langchain_core.documents import Document
from pipeline.state import GraphState

logger = logging.getLogger(__name__)

KEEP_THRESHOLD     = 0.4
SUFFICIENT_QUALITY = 0.6
PARTIAL_QUALITY    = 0.35


class CRAGNode:

    def __call__(self, state: GraphState) -> dict:
        query       = state.get("query", "")
        retrieved   = state.get("retrieved_docs", [])
        retry_count = state.get("retry_count", 0)

        if not retrieved:
            msg = "[crag] No docs to evaluate — marking insufficient"
            return {"filtered_docs": [], "retrieval_score": 0.0,
                    "answer_quality": "retry", "retry_count": retry_count + 1, "log": [msg]}

        scored = []
        for doc in retrieved:
            score, meta = self._score_chunk(query, doc)
            scored.append((doc, score, meta))
            doc.metadata["crag_score"]       = round(score, 4)
            doc.metadata["crag_reason"]      = meta.get("reason", "")
            doc.metadata["crag_has_numbers"] = meta.get("contains_numbers", False)
            doc.metadata["crag_entity"]      = meta.get("financial_entity", "none")

        kept = [(d, s, m) for d, s, m in scored if s >= KEEP_THRESHOLD]

        filtered_docs = [doc for doc, _, _ in kept]

        if not filtered_docs and scored:
            # everything scored below the bar, but empty context is worse
            filtered_docs = [doc for doc, _, _ in scored]
            avg_score = round(
                sum(doc.metadata.get("retrieval_score", 0.5)
                    for doc in filtered_docs) / len(filtered_docs), 3
            )
            verdict = "sufficient"
            logger.warning("[crag] Using all chunks with fallback scores")
        else:
            avg_score = round(sum(s for _, s, _ in kept) / len(kept), 3) if kept else 0.0
            verdict   = self._quality_verdict(avg_score, len(kept))

        msg = (
            f"[crag] kept={len(filtered_docs)}/{len(scored)}, "
            f"avg_score={avg_score:.3f}, verdict='{verdict}'"
        )
        logger.info(msg)

        new_retry = retry_count + 1 if verdict == "retry" else retry_count

        return {
            "filtered_docs":   filtered_docs,
            "retrieval_score": avg_score,
            "answer_quality":  verdict,
            "retry_count":     new_retry,
            "log":             [msg],
        }

    def _score_chunk(self, question: str, doc: Document):
        score = float(doc.metadata.get("retrieval_score", 0.5))
        score = max(0.0, min(1.0, score))
        return score, {
            "reason": "vector similarity score",
            "contains_numbers": any(ch.isdigit() for ch in doc.page_content),
            "financial_entity": "unknown",
        }

    @staticmethod
    def _quality_verdict(avg_score: float, n_kept: int) -> str:
        if n_kept == 0:
            return "retry"
        if avg_score >= SUFFICIENT_QUALITY:
            return "sufficient"
        if avg_score >= PARTIAL_QUALITY:
            return "partial"
        return "retry"


_crag = CRAGNode()

def crag_node(state: GraphState) -> dict:
    return _crag(state)
