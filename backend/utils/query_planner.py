from services.llm_service import get_llm
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings

logger = logging.getLogger(__name__)

COMPLEXITY_PROMPT = ChatPromptTemplate.from_template("""
You are a financial query planner. Decide if the question below is:
  - "simple"  : single focused question answerable from one section
  - "complex" : requires comparing multiple sections, time periods,
                or aggregating multiple data points

Respond with ONLY one word: simple or complex

Question: {question}
""")

DECOMPOSE_PROMPT = ChatPromptTemplate.from_template("""
You are a financial analyst. Break this complex question into
2-4 focused sub-questions. Each sub-question should be independently
answerable from a financial report.

Return ONLY the sub-questions, one per line, no numbering.

Question: {question}
""")

SYNTHESIS_PROMPT = ChatPromptTemplate.from_template("""
You are a senior financial analyst. You have answers to several
sub-questions that together answer a larger question.

Synthesize them into one coherent, well-structured final answer.
Use bullet points or sections if needed. Be specific with numbers.

ORIGINAL QUESTION:
{question}

SUB-QUESTION ANSWERS:
{sub_answers}

CONVERSATION HISTORY (for context):
{history}

Final synthesized answer:
""")


class QueryPlanner:
    
    def __init__(self):
        self._llm = get_llm(temperature=0.0)
        self._classifier  = COMPLEXITY_PROMPT  | self._llm | StrOutputParser()
        self._decomposer  = DECOMPOSE_PROMPT   | self._llm | StrOutputParser()
        self._synthesizer = SYNTHESIS_PROMPT   | self._llm | StrOutputParser()

    def classify(self, question: str) -> str:
        try:
            result  = self._classifier.invoke({"question": question})
            verdict = result.strip().lower()
            return "complex" if "complex" in verdict else "simple"
        except Exception as e:
            logger.warning(f"[planner] Classification failed: {e} — defaulting simple")
            return "simple"

    def decompose(self, question: str) -> list:
        try:
            raw  = self._decomposer.invoke({"question": question})
            subs = [l.strip() for l in raw.strip().split("\n") if l.strip()]
            logger.info(f"[planner] Decomposed into {len(subs)} sub-questions")
            return subs[:4]
        except Exception as e:
            logger.warning(f"[planner] Decomposition failed: {e}")
            return [question]

    def synthesize(self, question: str, sub_answers: list, history: str = "") -> str:
        sub_answers_str = "\n\n".join(
            f"Sub-question: {q}\nAnswer: {a}" for q, a in sub_answers
        )
        try:
            return self._synthesizer.invoke({
                "question":    question,
                "sub_answers": sub_answers_str,
                "history":     history or "None",
            }).strip()
        except Exception as e:
            logger.warning(f"[planner] Synthesis failed: {e}")
            return "\n\n".join(a for _, a in sub_answers)


query_planner = QueryPlanner()

