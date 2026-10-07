import logging
from services.pdf_service import PDFService
from pipeline.state import GraphState

logger = logging.getLogger(__name__)
_pdf_service = PDFService(upload_dir="data/uploads")


def loader_node(state: GraphState) -> dict:
    """
    LangGraph Node: Document Loader
    Reads:  state["file_path"]
    Writes: parsed_text, doc_metadata, doc_id, log
    """
    file_path = state.get("file_path", "")

    if not file_path:
        msg = "[loader] ERROR: no file_path provided"
        logger.error(msg)
        return {"parsed_text": "", "doc_metadata": {}, "log": [msg]}

    logger.info(f"loader_node: parsing '{file_path}'")

    try:
        parsed = _pdf_service.parse(file_path)
        log_entry = (
            f"[loader] Parsed '{parsed.file_name}' — "
            f"{parsed.total_pages} pages, "
            f"doc_id={parsed.doc_id[:8]}…, "
            f"chars={len(parsed.full_text):,}"
        )
        logger.info(log_entry)
        return {
            "parsed_text":  parsed.full_text,
            "doc_id":       parsed.doc_id,
            "doc_metadata": parsed.doc_metadata,
            "log":          [log_entry],
        }
    except FileNotFoundError as e:
        msg = f"[loader] ERROR: {e}"
        logger.error(msg)
        return {"parsed_text": "", "doc_metadata": {}, "log": [msg]}
    except Exception as e:
        msg = f"[loader] UNEXPECTED ERROR: {e}"
        logger.exception(msg)
        return {"parsed_text": "", "doc_metadata": {}, "log": [msg]}
