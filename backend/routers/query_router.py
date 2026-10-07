import json, uuid, time, logging, asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pipeline.runner import run_query
from utils.memory import memory_store
from utils.query_planner import query_planner
from utils.evaluator import evaluator
from utils.json_sanitize import json_safe

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    query:      str
    session_id: str = ""


class QueryResponse(BaseModel):
    answer:         str
    sources:        list
    confidence:     float
    metrics:        dict
    sub_questions:  list
    retry_count:    int
    session_id:     str
    docs_searched:  list    # which docs the router sent the query to
    routing_reason: str     # and why it chose those


@router.post("/query/stream")
async def query_stream(req: QueryRequest) -> StreamingResponse:
    session_id = req.session_id or str(uuid.uuid4())
    return StreamingResponse(
        _run_stream(req, session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _run_stream(req, session_id):
    def sse(event_type, data):
        return f"data: {json.dumps(json_safe({'type': event_type, **data}))}\n\n"

    try:
        session = memory_store.get_or_create(session_id, "multi-doc")
        history = session.format_history(n=3)

        yield sse("status", {"message": "Analyzing your question…"})
        await asyncio.sleep(0)

        complexity = await asyncio.get_event_loop().run_in_executor(
            None, query_planner.classify, req.query
        )
        yield sse("status", {"message": f"Query type: {complexity}"})
        await asyncio.sleep(0)

        yield sse("status", {"message": "Finding most relevant document(s)…"})
        await asyncio.sleep(0)

        t_start = time.time()

        if complexity == "simple":
            result = await _run_simple(req, history)
        else:
            yield sse("status", {"message": "Decomposing complex question…"})
            result = await _run_complex(req, history)
            for sq in result.get("sub_questions", []):
                yield sse("status", {"message": f"Researched: {sq[:60]}…"})
                await asyncio.sleep(0)

        latency_ms = (time.time() - t_start) * 1000

        for doc_info in result.get("docs_searched", []):
            yield sse("status", {
                "message": f"Searched: {doc_info.get('file_name', 'unknown')}"
            })
            await asyncio.sleep(0.05)

        if result.get("routing_reason"):
            yield sse("status", {"message": f"Routing: {result['routing_reason']}"})

        for log_entry in result.get("log", [])[-4:]:
            yield sse("status", {"message": log_entry})
            await asyncio.sleep(0.05)

        session.add_turn(
            question=req.query,
            answer=result.get("answer", ""),
            confidence=result.get("confidence", 0.0),
            doc_id="multi-doc",
        )

        evaluator.record(
            session_id=session_id,
            doc_id=",".join(
                d.get("doc_id", "")[:8]
                for d in result.get("docs_searched", [])
            ),
            query=req.query,
            complexity=complexity,
            pipeline_result=result,
            latency_ms=latency_ms,
        )

        run_id = evaluator._records[-1].run_id if evaluator._records else ""

        yield sse("answer", {
            "payload": {
                **result,
                "session_id":    session_id,
                "run_id":        run_id,
            }
        })

    except Exception as e:
        logger.exception("Query stream failed")
        yield sse("error", {"message": str(e)})


@router.post("/query", response_model=QueryResponse)
async def query_sync(req: QueryRequest) -> QueryResponse:
    session_id = req.session_id or str(uuid.uuid4())
    session    = memory_store.get_or_create(session_id, "multi-doc")
    history    = session.format_history(n=3)
    complexity = query_planner.classify(req.query)

    result = await _run_simple(req, history) if complexity == "simple" \
             else await _run_complex(req, history)

    session.add_turn(
        question=req.query,
        answer=result.get("answer", ""),
        confidence=result.get("confidence", 0.0),
        doc_id="multi-doc",
    )
    result = json_safe(result)
    return QueryResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        confidence=result.get("confidence", 0.0),
        metrics=result.get("metrics", {}),
        sub_questions=result.get("sub_questions", []),
        retry_count=result.get("retry_count", 0),
        session_id=session_id,
        docs_searched=result.get("docs_searched", []),
        routing_reason=result.get("routing_reason", ""),
    )


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    memory_store.clear(session_id)
    return {"cleared": True, "session_id": session_id}


@router.get("/session/{session_id}/history")
def get_history(session_id: str):
    session = memory_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "turns": [
            {"question": t.question, "answer": t.answer[:200] + "…",
             "confidence": t.confidence, "timestamp": t.timestamp}
            for t in session.turns
        ],
    }


async def _run_simple(req, history: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_query(
            query=_inject_history(req.query, history)
        )
    )


async def _run_complex(req, history: str) -> dict:
    loop          = asyncio.get_event_loop()
    sub_questions = await loop.run_in_executor(
        None, query_planner.decompose, req.query
    )
    sub_answers = []
    all_sources = []
    all_logs    = []
    all_docs    = []

    for sq in sub_questions:
        sub_result = await loop.run_in_executor(
            None, lambda q=sq: run_query(query=q)
        )
        sub_answers.append((sq, sub_result.get("answer", "")))
        all_sources.extend(sub_result.get("sources", []))
        all_logs.extend(sub_result.get("log", []))
        all_docs.extend(sub_result.get("docs_searched", []))

    final = await loop.run_in_executor(
        None, lambda: query_planner.synthesize(req.query, sub_answers, history)
    )

    # sub-questions overlap a lot, so trim duplicate citations
    seen_src  = set()
    uniq_src  = []
    for s in all_sources:
        key = (s.get("section"), s.get("page"), s.get("source_doc_id"))
        if key not in seen_src:
            seen_src.add(key)
            uniq_src.append(s)

    seen_docs = set()
    uniq_docs = []
    for d in all_docs:
        if d.get("doc_id") not in seen_docs:
            seen_docs.add(d.get("doc_id"))
            uniq_docs.append(d)

    return {
        "answer": final, "sources": uniq_src, "confidence": 0.8,
        "metrics": {}, "sub_questions": sub_questions,
        "retry_count": 0, "log": all_logs,
        "docs_searched": uniq_docs, "routing_reason": "multi-step decomposition",
    }


def _inject_history(query: str, history: str) -> str:
    if not history or history == "No prior conversation.":
        return query
    return f"[Conversation history]\n{history}\n\n[Current question]\n{query}"
