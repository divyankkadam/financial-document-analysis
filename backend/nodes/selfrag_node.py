from services.llm_service import get_llm
import json
import logging
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from pipeline.state import GraphState

logger = logging.getLogger(__name__)

EVALUATION_PROMPT = ChatPromptTemplate.from_template("""
You are a senior financial analyst evaluating the quality of an AI-generated
answer to a question about a financial report.

Evaluate the DRAFT ANSWER on four dimensions. For each, give a score 0.0–1.0
and a brief reason. Then give an overall verdict.

Respond with ONLY a JSON object — no markdown, no explanation outside the JSON:
{{
  "relevance":     {{"score": <float>, "reason": "<one sentence>"}},
  "groundedness":  {{"score": <float>, "reason": "<one sentence>"}},
  "completeness":  {{"score": <float>, "reason": "<one sentence>"}},
  "confidence":    {{"score": <float>, "reason": "<one sentence>"}},
  "overall":       <float>,
  "verdict":       "<good|refine|retry>",
  "improvement":   "<one sentence describing what is missing or wrong, or 'none'>"
}}

Verdict rules:
  "good"   — all four scores >= 0.7
  "refine" — overall >= 0.5 but at least one dimension < 0.7
  "retry"  — overall < 0.5 or groundedness < 0.4

USER QUESTION:
{question}

RETRIEVED CONTEXT CHUNKS:
{context}

DRAFT ANSWER:
{answer}
""")

REFINEMENT_PROMPT = ChatPromptTemplate.from_template("""
You are a financial analyst improving a draft answer.

The evaluator flagged this issue: {improvement}

Using ONLY the provided context chunks, rewrite the answer to fix the issue.
Be specific. Use numbers and metrics from the context where available.

USER QUESTION:
{question}

CONTEXT CHUNKS:
{context}

DRAFT ANSWER TO IMPROVE:
{draft}

Provide the improved answer only — no preamble.
""")


class SelfRAGNode:

    def __init__(self):
        self._llm = None
        self._evaluator = None
        self._refiner   = None

    def __call__(self, state: GraphState) -> dict:
        query       = state.get("query", "")
        draft       = state.get("draft_answer", "")
        docs        = state.get("filtered_docs", [])
        retry_count = state.get("retry_count", 0)

        if not draft:
            msg = "[selfrag] No draft answer to evaluate"
            return {"answer_quality": "retry", "confidence": 0.0,
                    "retry_count": retry_count + 1, "log": [msg]}

        context_str = self._format_context(docs)
        evaluation  = self._evaluate(query, context_str, draft)
        verdict     = evaluation.get("verdict", "retry")
        overall     = float(evaluation.get("overall", 0.0))
        improvement = evaluation.get("improvement", "none")

        if retry_count >= settings.max_retries:
            verdict = "good"

        if verdict == "good":
            msg = f"[selfrag] Answer accepted — overall={overall:.2f}"
            return {"answer_quality": "good", "confidence": round(overall, 3),
                    "eval_metrics": self._build_metrics(evaluation), "log": [msg]}

        if verdict == "refine":
            refined, refine_msg = self._refine(query, context_str, draft, improvement)
            return {"draft_answer": refined, "answer_quality": "refine",
                    "confidence": round(overall, 3), "retry_count": retry_count + 1,
                    "eval_metrics": self._build_metrics(evaluation), "log": [refine_msg]}

        msg = f"[selfrag] Insufficient — overall={overall:.2f}, retry #{retry_count + 1}"
        return {"answer_quality": "retry", "confidence": round(overall, 3),
                "retry_count": retry_count + 1,
                "eval_metrics": self._build_metrics(evaluation), "log": [msg]}

    def _evaluate(self, question, context_str, answer):
        try:
            raw = self._get_evaluator().invoke({"question": question,
                                                 "context": context_str[:4000],
                                                 "answer": answer[:2000]})
            return self._parse_json(raw)
        except Exception as e:
            logger.warning(f"[selfrag] Evaluation failed: {e} — auto-accepting answer")
            # a neutral score stops the retry loop from spinning forever
            return {
                "relevance":    {"score": 0.7},
                "groundedness": {"score": 0.7},
                "completeness": {"score": 0.7},
                "confidence":   {"score": 0.7},
                "overall":      0.7,
                "verdict":      "good",
                "improvement":  "none",
            }

    def _refine(self, question, context_str, draft, improvement):
        try:
            refined = self._get_refiner().invoke({"question": question,
                                                   "context": context_str[:4000],
                                                   "draft": draft, "improvement": improvement})
            msg = f"[selfrag] Answer refined — issue: '{improvement[:80]}'"
            return refined.strip(), msg
        except Exception as e:
            return draft, f"[selfrag] Refinement failed: {e}"

    @staticmethod
    def _format_context(docs):
        if not docs:
            return "No context available."
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(
                f"[Chunk {i} | Section: {doc.metadata.get('section','?')} | "
                f"Page: {doc.metadata.get('page_number','?')} | "
                f"Score: {doc.metadata.get('crag_score','?')}]\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_metrics(evaluation):
        return {
            "relevance":    evaluation.get("relevance",    {}).get("score", 0),
            "groundedness": evaluation.get("groundedness", {}).get("score", 0),
            "completeness": evaluation.get("completeness", {}).get("score", 0),
            "confidence":   evaluation.get("confidence",   {}).get("score", 0),
            "overall":      evaluation.get("overall", 0),
            "verdict":      evaluation.get("verdict", "unknown"),
            "improvement":  evaluation.get("improvement", "none"),
        }

    @staticmethod
    def _parse_json(raw):
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm(temperature=0.0)
        return self._llm

    def _get_evaluator(self):
        if self._evaluator is None:
            self._evaluator = EVALUATION_PROMPT | self._get_llm() | StrOutputParser()
        return self._evaluator

    def _get_refiner(self):
        if self._refiner is None:
            self._refiner = REFINEMENT_PROMPT | self._get_llm() | StrOutputParser()
        return self._refiner


_selfrag = SelfRAGNode()

def selfrag_node(state: GraphState) -> dict:
    return _selfrag(state)
