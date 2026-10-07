import logging
from services.chunker_service import ChunkerService
from services.vectorstore_service import get_vectorstore_service
from pipeline.state import GraphState

logger  = logging.getLogger(__name__)
_chunker = ChunkerService()


def chunker_node(state: GraphState) -> dict:
    """
    LangGraph Node: Chunking + Embedding
    Reads:  parsed_text, doc_id, doc_metadata
    Writes: chunks, embeddings_done, log
    """
    parsed_text  = state.get("parsed_text", "")
    doc_id       = state.get("doc_id", "unknown")
    file_name    = state.get("file_path", "").split("/")[-1]
    doc_metadata = state.get("doc_metadata", {})

    if not parsed_text.strip():
        msg = "[chunker] ERROR: parsed_text is empty"
        logger.error(msg)
        return {"chunks": [], "embeddings_done": False, "log": [msg]}

    chunks = _chunker.chunk(
        text=parsed_text,
        doc_id=doc_id,
        file_name=file_name,
        doc_metadata=doc_metadata,
    )

    if not chunks:
        msg = "[chunker] ERROR: zero chunks produced"
        return {"chunks": [], "embeddings_done": False, "log": [msg]}

    try:
        vs = get_vectorstore_service()
        vs.add_documents(doc_id=doc_id, documents=chunks)
        embeddings_done = True
        msg = f"[chunker] {len(chunks)} chunks embedded for doc_id={doc_id[:8]}…"
    except Exception as e:
        logger.exception("Embedding/storage failed")
        embeddings_done = False
        msg = f"[chunker] Embedding failed: {e}"

    logger.info(msg)
    return {"chunks": chunks, "embeddings_done": embeddings_done, "log": [msg]}
