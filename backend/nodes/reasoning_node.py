from services.llm_service import get_llm
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pipeline.state import GraphState

logger = logging.getLogger(__name__)

REASONING_PROMPT = ChatPromptTemplate.from_template("""
You are a senior financial analyst. Answer the user's question using ONLY
the provided context chunks from a financial report.

Rules:
- Cite specific numbers, percentages, and figures wherever available
- If comparing across years or segments, present data in a structured way
- If the context is insufficient, say what is missing — do not hallucinate
- Be concise but complete; use bullet points for multi-part answers
- If a prior draft exists, use it as a starting point and improve it

USER QUESTION:
{question}

CONTEXT CHUNKS:
{context}

PRIOR DRAFT (if any):
{draft}

Your answer:
""")

class ReasoningNode:
    
    def __init__(self):
        self._llm = None
        self._reasoner = None
    

    def __call__(self, state: GraphState) -> dict:
        query = state.get("query", "")
        docs  = state.get("filtered_docs", [])
        draft = state.get("draft_answer", "")

        if not docs:
            msg = "[reasoning] No filtered docs — cannot reason"
            return {"draft_answer": "", "log": [msg]}

        context_str   = self._format_context(docs)

        answer = self._get_reasoner().invoke({
            "question": query,
            "context":  context_str,
            "draft":    draft or "None",
        })

        msg = f"[reasoning] Draft generated — {len(answer)} chars"
        logger.info(msg)
        return {"draft_answer": answer.strip(), "sub_questions": [query], "log": [msg]}

    @staticmethod
    def _format_context(docs: list) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            parts.append(
                f"[Chunk {i} | {meta.get('section','?')} | "
                f"p.{meta.get('page_number','?')} | "
                f"score={meta.get('crag_score','?')}]\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(parts)

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm(temperature=0.0)
        return self._llm

    def _get_reasoner(self):
        if self._reasoner is None:
            self._reasoner = REASONING_PROMPT | self._get_llm() | StrOutputParser()
        return self._reasoner


_reasoning = ReasoningNode()

def reasoning_node(state: GraphState) -> dict:
    return _reasoning(state)
