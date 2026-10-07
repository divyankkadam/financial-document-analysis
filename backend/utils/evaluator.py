import uuid
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from collections import defaultdict
from utils.json_sanitize import json_safe

logger = logging.getLogger(__name__)
EVAL_LOG_PATH = Path("logs/eval.jsonl")


@dataclass
class EvaluationRecord:
    run_id:           str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id:       str   = ""
    doc_id:           str   = ""
    timestamp:        float = field(default_factory=time.time)
    query:            str   = ""
    complexity:       str   = ""
    n_retrieved:      int   = 0
    n_filtered:       int   = 0
    retrieval_score:  float = 0.0
    crag_verdict:     str   = ""
    crag_avg_score:   float = 0.0
    selfrag_verdict:  str   = ""
    selfrag_scores:   dict  = field(default_factory=dict)
    retry_count:      int   = 0
    answer_length:    int   = 0
    confidence:       float = 0.0
    n_sources:        int   = 0
    latency_ms:       float = 0.0
    pipeline_log:     list  = field(default_factory=list)


class PipelineEvaluator:
    def __init__(self):
        self._records: list = []
        EVAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def record(self, session_id, doc_id, query, complexity,
               pipeline_result, latency_ms) -> EvaluationRecord:
        metrics = pipeline_result.get("metrics", {})
        rec = EvaluationRecord(
            session_id=session_id, doc_id=doc_id, query=query,
            complexity=complexity,
            retrieval_score=json_safe(pipeline_result.get("retrieval_score", 0.0)),
            crag_verdict=metrics.get("crag_verdict", ""),
            crag_avg_score=json_safe(pipeline_result.get("retrieval_score", 0.0)),
            selfrag_verdict=metrics.get("verdict", ""),
            selfrag_scores={
                "relevance":    metrics.get("relevance", 0),
                "groundedness": metrics.get("groundedness", 0),
                "completeness": metrics.get("completeness", 0),
                "confidence":   metrics.get("confidence", 0),
            },
            retry_count=pipeline_result.get("retry_count", 0),
            answer_length=len(pipeline_result.get("answer", "")),
            confidence=json_safe(pipeline_result.get("confidence", 0.0)),
            n_sources=len(pipeline_result.get("sources", [])),
            latency_ms=round(latency_ms, 2),
            n_retrieved=len(pipeline_result.get("sources", [])),
            n_filtered=len(pipeline_result.get("sources", [])),
            pipeline_log=json_safe(pipeline_result.get("log", [])),
        )
        self._records.append(rec)
        self._persist(rec)
        logger.info(f"[eval] run_id={rec.run_id} confidence={rec.confidence:.2f} "
                    f"retries={rec.retry_count} latency={rec.latency_ms}ms")
        return rec

    def get_stats(self, doc_id: Optional[str] = None) -> dict:
        recs = [r for r in self._records if not doc_id or r.doc_id == doc_id]
        if not recs:
            return {"total_queries": 0}
        confidences  = [r.confidence for r in recs]
        latencies    = [r.latency_ms for r in recs]
        retry_counts = [r.retry_count for r in recs]
        verdict_dist: dict = defaultdict(int)
        for r in recs:
            verdict_dist[r.selfrag_verdict or "unknown"] += 1
        complexity_dist: dict = defaultdict(int)
        for r in recs:
            complexity_dist[r.complexity or "unknown"] += 1
        return {
            "total_queries":   len(recs),
            "avg_confidence":  round(sum(confidences) / len(confidences), 3),
            "avg_latency_ms":  round(sum(latencies) / len(latencies), 1),
            "avg_retries":     round(sum(retry_counts) / len(retry_counts), 2),
            "p95_latency_ms":  round(sorted(latencies)[int(len(latencies)*0.95)], 1),
            "verdict_dist":    dict(verdict_dist),
            "complexity_dist": dict(complexity_dist),
            "high_confidence": sum(1 for c in confidences if c >= 0.8),
            "low_confidence":  sum(1 for c in confidences if c < 0.5),
        }

    def get_recent(self, n: int = 20, doc_id: Optional[str] = None) -> list:
        recs = [r for r in self._records if not doc_id or r.doc_id == doc_id]
        return [asdict(r) for r in recs[-n:]]

    def get_run(self, run_id: str) -> Optional[dict]:
        for r in self._records:
            if r.run_id == run_id:
                return asdict(r)
        return None

    def _persist(self, rec: EvaluationRecord) -> None:
        try:
            with open(EVAL_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_safe(asdict(rec))) + "\n")
        except Exception as e:
            logger.warning(f"[eval] Persist failed: {e}")

    def load_from_disk(self) -> int:
        if not EVAL_LOG_PATH.exists():
            return 0
        loaded = 0
        with open(EVAL_LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._records.append(EvaluationRecord(**data))
                    loaded += 1
                except Exception:
                    pass
        logger.info(f"[eval] Loaded {loaded} records from disk")
        return loaded


evaluator = PipelineEvaluator()
