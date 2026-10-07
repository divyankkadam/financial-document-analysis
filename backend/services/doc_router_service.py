from services.llm_service import get_llm

import logging
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.embedding_service import get_embedding_service
import numpy as np
import json

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path("data/doc_registry.json")

DOC_SELECTION_PROMPT = ChatPromptTemplate.from_template("""
You are a financial document routing assistant.

Given a USER QUERY and a list of AVAILABLE DOCUMENTS (with their titles,
metadata, and a short preview), decide which document(s) are most likely
to contain the answer.

Return ONLY a JSON array of doc_ids in order of relevance, most relevant first.
Return at most {max_docs} doc_ids. If only one document is relevant, return one.

Example response: ["doc_id_1", "doc_id_2"]

USER QUERY:
{query}

AVAILABLE DOCUMENTS:
{doc_summaries}
""")


class DocRouterService:
    """
    Picks the doc(s) worth searching for a query.

    Embeddings do the cheap filtering (top 5 by cosine), then the LLM looks
    at just those and decides which actually answer the question.
    """

    def __init__(self):
        self._vs         = None
        self._embeddings = None
        self._selector   = None

    def select_docs(
        self,
        query:    str,
        max_docs: int = 2,
    ) -> list[dict]:
        """
        Given a query, return the most relevant doc(s) from the registry.
        Returns list of doc dicts sorted by relevance (most relevant first).
        """
        registry = self._load_registry()
        if not registry:
            logger.warning("[doc_router] No documents in registry")
            return []

        docs = list(registry.values())

        # nothing to disambiguate, skip the whole ranking path
        if len(docs) == 1:
            logger.info("[doc_router] Only one doc — auto-selecting it")
            return docs

        shortlist = self._embedding_shortlist(query, docs, top_k=min(5, len(docs)))
        logger.info(f"[doc_router] Shortlist: {[d['file_name'] for d in shortlist]}")

        selected = self._llm_rerank(query, shortlist, max_docs=max_docs)
        logger.info(f"[doc_router] Selected: {[d['file_name'] for d in selected]}")

        return selected

    def select_single_doc(self, query: str) -> dict | None:
        """Convenience — returns only the single best doc."""
        results = self.select_docs(query, max_docs=1)
        return results[0] if results else None

    def _embedding_shortlist(
        self,
        query: str,
        docs:  list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Cosine similarity between the query and each doc's preview text.
        Falls back to the raw doc list if the embedder blows up.
        """
        try:
            query_vec = np.array(self._get_embeddings().embed_query(query))

            scored = []
            for doc in docs:
                # title + preview is a decent stand-in for the whole document
                preview_text = (
                    f"{doc.get('file_name', '')} "
                    f"{doc.get('metadata', {}).get('title', '')} "
                    f"{doc.get('preview', '')}"
                )
                doc_vec = np.array(
                    self._get_embeddings().embed_query(preview_text[:1000])
                )

                sim = float(
                    np.dot(query_vec, doc_vec) /
                    (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-9)
                )
                scored.append((doc, sim))
                doc["_embedding_score"] = round(sim, 4)

            scored.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in scored[:top_k]]

        except Exception as e:
            logger.warning(f"[doc_router] Embedding shortlist failed: {e} — using all docs")
            return docs[:top_k]

    def _llm_rerank(
        self,
        query:    str,
        docs:     list[dict],
        max_docs: int = 2,
    ) -> list[dict]:
        """
        Ask the LLM to pick the most relevant doc(s) from the shortlist.
        Falls back to embedding ranking if LLM fails.
        """
        doc_summaries = "\n\n".join([
            f"doc_id: {d['doc_id']}\n"
            f"file:   {d['file_name']}\n"
            f"pages:  {d.get('total_pages', '?')}\n"
            f"title:  {d.get('metadata', {}).get('title', 'N/A')}\n"
            f"preview: {d.get('preview', '')[:300]}"
            for d in docs
        ])

        try:
            raw = self._get_selector().invoke({
                "query":        query,
                "doc_summaries": doc_summaries,
                "max_docs":     max_docs,
            })

            selected_ids = self._parse_json_list(raw)

            # the LLM orders by relevance, so keep its order
            id_to_doc = {d["doc_id"]: d for d in docs}
            selected  = [
                id_to_doc[did]
                for did in selected_ids
                if did in id_to_doc
            ][:max_docs]

            return selected if selected else docs[:max_docs]

        except Exception as e:
            logger.warning(f"[doc_router] LLM rerank failed: {e} — using embedding order")
            return docs[:max_docs]

    @staticmethod
    def _load_registry() -> dict:
        if REGISTRY_PATH.exists():
            try:
                return json.loads(REGISTRY_PATH.read_text())
            except Exception:
                return {}
        return {}

    @staticmethod
    def _parse_json_list(raw: str) -> list:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []

    def _get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embedding_service().model
        return self._embeddings

    def _get_selector(self):
        if self._selector is None:
            self._selector = DOC_SELECTION_PROMPT | get_llm(temperature=0.0) | StrOutputParser()
        return self._selector


doc_router = DocRouterService()
