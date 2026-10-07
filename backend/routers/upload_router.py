from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List

from services.pdf_service import PDFService
from services.chunker_service import ChunkerService
from services.vectorstore_service import get_vectorstore_service

import logging
import json
from pathlib import Path

router    = APIRouter(prefix="/api", tags=["upload"])

logger    = logging.getLogger(__name__)
_pdf_svc  = PDFService(upload_dir="data/uploads")
_chunker  = ChunkerService()

REGISTRY_PATH = Path("data/doc_registry.json")


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_registry(registry: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))


def _ingest_document(parsed, saved_path: Path):
    """
    Parse -> chunk -> embed -> store in Neo4j GraphRAG.
    Called after every upload to ensure index is ready for queries.
    """
    try:
        logger.info(f"[upload] Starting ingestion for '{parsed.file_name}'…")

        chunks = _chunker.chunk(
            text=parsed.full_text,
            doc_id=parsed.doc_id,
            file_name=parsed.file_name,
            doc_metadata=parsed.doc_metadata,
        )

        if not chunks:
            logger.warning(f"[upload] No chunks produced for '{parsed.file_name}'")
            return 0

        vs    = get_vectorstore_service()
        vs.add_document_structure(parsed)
        total = vs.add_documents(doc_id=parsed.doc_id, documents=chunks)

        logger.info(
            f"[upload] Ingestion complete — "
            f"'{parsed.file_name}': {len(chunks)} chunks, "
            f"{total} vectors stored"
        )
        return len(chunks)

    except Exception as e:
        logger.exception(f"[upload] Ingestion failed for '{parsed.file_name}': {e}")
        return 0


@router.post("/upload")
async def upload_pdf( file: UploadFile = File(...), background_tasks: BackgroundTasks = None, ) -> JSONResponse:

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit.")

    try:
        contents   = await file.read()
        saved_path = _pdf_svc.save_upload(contents, file.filename)
        parsed     = _pdf_svc.parse(saved_path)

        # ingest inline rather than as a background task so the doc is
        # searchable the moment the client gets its response
        chunk_count = _ingest_document(parsed, saved_path)

        registry = _load_registry()
        registry[parsed.doc_id] = {
            "doc_id":       parsed.doc_id,
            "file_name":    parsed.file_name,
            "file_path":    str(saved_path),
            "total_pages":  parsed.total_pages,
            "metadata":     parsed.doc_metadata,
            "preview":      parsed.full_text[:300],
            "chunk_count":  chunk_count,
            "indexed":      chunk_count > 0,
        }
        _save_registry(registry)

        return JSONResponse({
            "status":       "ok",
            "doc_id":       parsed.doc_id,
            "file_name":    parsed.file_name,
            "file_path":    str(saved_path),
            "total_pages":  parsed.total_pages,
            "chunk_count":  chunk_count,
            "indexed":      chunk_count > 0,
            "metadata":     parsed.doc_metadata,
            "preview":      parsed.full_text[:500],
        })

    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch")
async def upload_multiple_pdfs( files: List[UploadFile] = File(...)) -> JSONResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results  = []
    errors   = []
    registry = _load_registry()

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            errors.append({"file": file.filename, "error": "Not a PDF"})
            continue
        if file.size and file.size > 50 * 1024 * 1024:
            errors.append({"file": file.filename, "error": "Exceeds 50MB"})
            continue

        try:
            contents   = await file.read()
            saved_path = _pdf_svc.save_upload(contents, file.filename)
            parsed     = _pdf_svc.parse(saved_path)

            chunk_count = _ingest_document(parsed, saved_path)

            doc_entry = {
                "doc_id":       parsed.doc_id,
                "file_name":    parsed.file_name,
                "file_path":    str(saved_path),
                "total_pages":  parsed.total_pages,
                "metadata":     parsed.doc_metadata,
                "preview":      parsed.full_text[:300],
                "chunk_count":  chunk_count,
                "indexed":      chunk_count > 0,
            }
            registry[parsed.doc_id] = doc_entry
            results.append(doc_entry)

        except Exception as e:
            logger.exception(f"Failed to process {file.filename}")
            errors.append({"file": file.filename, "error": str(e)})

    _save_registry(registry)

    return JSONResponse({
        "status":    "ok",
        "uploaded":  len(results),
        "failed":    len(errors),
        "documents": results,
        "errors":    errors,
    })


@router.post("/documents/{doc_id}/reindex")
def reindex_document(doc_id: str) -> JSONResponse:
    """
    Force re-embed a document that was uploaded but not indexed.
    Useful to fix the 'no index found' error on existing uploads.
    """
    registry = _load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail="Document not found in registry")

    doc_info   = registry[doc_id]
    file_path  = Path(doc_info["file_path"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    try:
        parsed      = _pdf_svc.parse(file_path)
        chunk_count = _ingest_document(parsed, file_path)

        registry[doc_id]["chunk_count"] = chunk_count
        registry[doc_id]["indexed"]     = chunk_count > 0
        _save_registry(registry)

        return JSONResponse({
            "status":      "ok",
            "doc_id":      doc_id,
            "chunk_count": chunk_count,
            "indexed":     chunk_count > 0,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
def list_documents() -> JSONResponse:
    registry = _load_registry()
    return JSONResponse({
        "total":     len(registry),
        "documents": list(registry.values()),
    })


@router.get("/documents/{doc_id}")
def get_document(doc_id: str) -> JSONResponse:
    registry = _load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail="Document not found")
    return JSONResponse(registry[doc_id])


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> JSONResponse:
    registry = _load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail="Document not found")

    vs = get_vectorstore_service()
    vs.delete(doc_id)

    file_path = Path(registry[doc_id].get("file_path", ""))
    if file_path.exists():
        file_path.unlink()

    del registry[doc_id]
    _save_registry(registry)

    return JSONResponse({"deleted": True, "doc_id": doc_id})


@router.get("/index/{doc_id}/stats")
def index_stats(doc_id: str):
    vs = get_vectorstore_service()
    return vs.get_index_stats(doc_id)


@router.get("/indexes")
def list_indexes():
    vs = get_vectorstore_service()
    return {"indexes": vs.list_indexes()}
