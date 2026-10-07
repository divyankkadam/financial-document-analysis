import hashlib
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from services.vectorstore_service import get_vectorstore_service

logger = logging.getLogger(__name__)

QUERY_EXPANSION_PROMPT = ChatPromptTemplate.from_template("""
You are a financial analyst. Generate {n} different search queries for:
{question}
Return ONLY queries, one per line, no numbering.
""")


class RetrieverService:
    def __init__(self):
        self._vs  = get_vectorstore_service()
        self._llm = None   # lazy load - don't crash on startup

    def _get_llm(self):
        if self._llm is None:
            from services.llm_service import get_llm
            self._llm = get_llm(temperature=0.1)
        return self._llm

    def retrieve(
        self,
        doc_id:          str,
        query:           str,
        k:               int   = 6,
        expand_queries:  bool  = True,
        n_expansions:    int   = 2,
        score_threshold: float = 0.0,   # 0.0 = return all results
    ) -> list:
        queries = [query]

        # expansion is a nice-to-have, a failure here shouldn't kill the search
        if expand_queries:
            try:
                expanded = self._expand_query(query, n=n_expansions)
                queries.extend(expanded)
            except Exception as e:
                logger.warning(f"Query expansion skipped: {e}")

        all_results = []
        for q in queries:
            results = self._vs.search(
                doc_id=doc_id,
                query=q,
                k=k,
                score_threshold=score_threshold,  # 0.0 = no filtering
            )
            all_results.extend(results)

        final = self._deduplicate_and_rerank(all_results, top_k=k)
        logger.info(f"retrieve: raw={len(all_results)} → deduped={len(final)}")
        return final

    def retrieve_documents(self, doc_id: str, query: str, k: int = 6) -> list:
        return [doc for doc, _ in self.retrieve(doc_id, query, k)]

    def _expand_query(self, query: str, n: int = 2) -> list:
        chain = QUERY_EXPANSION_PROMPT | self._get_llm() | StrOutputParser()
        raw   = chain.invoke({"question": query, "n": n})
        return [l.strip() for l in raw.strip().split("\n") if l.strip()][:n]

    @staticmethod
    def _deduplicate_and_rerank(results: list, top_k: int = 6) -> list:
        seen = {}
        best = {}
        for doc, score in results:
            h = hashlib.md5(doc.page_content.encode()).hexdigest()
            if h not in seen or score < seen[h]:  # L2 distance: lower = better
                seen[h] = score
                best[h] = (doc, score)
        return sorted(best.values(), key=lambda x: x[1])[:top_k]  # ascending for L2