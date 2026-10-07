import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document



def test_chunker_produces_documents():
    from services.chunker_service import ChunkerService
    svc    = ChunkerService()
    chunks = svc.chunk(
        text="Revenue grew 12% YoY.\n\nRisk Factors\nCurrency risk is high.",
        doc_id="test-doc",
        file_name="test.pdf",
    )
    assert len(chunks) > 0
    assert all(hasattr(c, "page_content") for c in chunks)
    assert all("doc_id" in c.metadata for c in chunks)


def test_chunker_detects_sections():
    from services.chunker_service import ChunkerService
    svc    = ChunkerService()
    chunks = svc.chunk(
        text="Revenue\nRevenue grew 12%.\n\nRisk Factors\nCurrency risk.",
        doc_id="test-doc",
        file_name="test.pdf",
    )
    sections = {c.metadata.get("section") for c in chunks}
    assert len(sections) >= 1



def test_crag_empty_docs():
    from nodes.crag_node import crag_node
    result = crag_node({
        "query": "What is revenue?",
        "retrieved_docs": [],
        "retry_count": 0,
        "log": [],
    })
    assert result["answer_quality"] == "retry"
    assert result["filtered_docs"] == []



def test_selfrag_no_draft():
    from nodes.selfrag_node import selfrag_node
    result = selfrag_node({
        "query":         "What is revenue?",
        "draft_answer":  "",
        "filtered_docs": [],
        "retry_count":   0,
        "log":           [],
    })
    assert result["answer_quality"] == "retry"



def test_answer_node_formats_sources():
    import json
    from nodes.answer_node import answer_node
    doc = Document(
        page_content="Revenue grew 12%.",
        metadata={"section": "Revenue", "page_number": 5, "crag_score": 0.9},
    )
    result = answer_node({
        "query":         "Revenue?",
        "draft_answer":  "Revenue grew 12%.",
        "filtered_docs": [doc],
        "eval_metrics":  {},
        "confidence":    0.9,
        "log":           [],
    })
    payload = json.loads(result["final_answer"])
    assert payload["answer"] == "Revenue grew 12%."
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["section"] == "Revenue"



def test_route_after_crag_retry():
    from pipeline.graph import route_after_crag
    assert route_after_crag({"answer_quality": "retry", "retry_count": 0}) == "retriever_node"


def test_route_after_crag_sufficient():
    from pipeline.graph import route_after_crag
    assert route_after_crag({"answer_quality": "sufficient", "retry_count": 0}) == "reasoning_node"


def test_route_after_selfrag_good():
    from pipeline.graph import route_after_selfrag
    assert route_after_selfrag({"answer_quality": "good", "retry_count": 0}) == "final_answer_node"


def test_route_after_selfrag_max_retries():
    from pipeline.graph import route_after_selfrag
    assert route_after_selfrag({"answer_quality": "retry", "retry_count": 3}) == "final_answer_node"



def test_memory_session_lifecycle():
    from utils.memory import MemoryStore
    store   = MemoryStore()
    session = store.get_or_create("sess-001", "doc-abc")
    session.add_turn("What is revenue?", "Revenue grew 12%.", 0.9, "doc-abc")
    assert len(session.turns) == 1
    assert "Revenue" in session.format_history()
    store.clear("sess-001")
    assert store.get("sess-001") is None



def test_evaluator_record_and_stats():
    from utils.evaluator import PipelineEvaluator
    ev = PipelineEvaluator()
    ev.record(
        session_id="s1", doc_id="d1", query="test query",
        complexity="simple",
        pipeline_result={
            "answer": "Test answer", "sources": [], "confidence": 0.85,
            "metrics": {}, "retry_count": 0, "retrieval_score": 0.7, "log": [],
        },
        latency_ms=1200.0,
    )
    stats = ev.get_stats()
    assert stats["total_queries"] == 1
    assert stats["avg_confidence"] == 0.85
