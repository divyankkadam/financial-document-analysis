import fitz  # PyMuPDF
import pdfplumber
import hashlib
import re
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    tables: list
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    file_name: str
    file_path: str
    doc_id: str
    total_pages: int
    pages: list
    doc_metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(
            f"[Page {p.page_number}]\n{p.text}"
            for p in self.pages
            if p.text.strip()
        )


class PDFService:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, file_bytes: bytes, filename: str) -> Path:
        safe_name = Path(filename).name
        dest = self.upload_dir / safe_name
        dest.write_bytes(file_bytes)
        logger.info(f"Saved upload: {dest}")
        return dest

    def parse(self, file_path) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        doc_id   = self._hash_file(path)
        pages    = self._extract_pages(path)
        doc_meta = self._extract_doc_metadata(path)

        logger.info(f"Parsed '{path.name}' — {len(pages)} pages, doc_id={doc_id[:8]}…")

        return ParsedDocument(
            file_name=path.name,
            file_path=str(path),
            doc_id=doc_id,
            total_pages=len(pages),
            pages=pages,
            doc_metadata=doc_meta,
        )

    def _extract_pages(self, path: Path) -> list:
        text_by_page  = self._extract_text_pymupdf(path)
        table_by_page = self._extract_tables_pdfplumber(path)

        pages = []
        for page_num, text in text_by_page.items():
            pages.append(PageContent(
                page_number=page_num,
                text=self._clean_text(text),
                tables=table_by_page.get(page_num, []),
                metadata={"page": page_num},
            ))
        return sorted(pages, key=lambda p: p.page_number)

    def _extract_text_pymupdf(self, path: Path) -> dict:
        result = {}
        try:
            doc = fitz.open(str(path))

            # owner-password PDFs show up often, empty password unlocks those
            if doc.is_encrypted:
                if not doc.authenticate(""):
                    logger.warning(f"PDF is encrypted and password-protected: {path.name}")
                    doc.close()
                    return {}

            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                page_text = "\n".join(
                    b[4] for b in blocks if b[6] == 0
                )
                result[page.number + 1] = page_text
            doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed for {path.name}: {e}")
        return result

    def _extract_tables_pdfplumber(self, path: Path) -> dict:
        result = {}
        try:
            with pdfplumber.open(str(path)) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    if tables:
                        result[i] = tables
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        return result

    def _extract_doc_metadata(self, path: Path) -> dict:
        meta = {}
        try:
            with fitz.open(str(path)) as doc:
                raw = doc.metadata or {}
                meta = {
                    "title":    raw.get("title", ""),
                    "author":   raw.get("author", ""),
                    "subject":  raw.get("subject", ""),
                    "keywords": raw.get("keywords", ""),
                    "created":  raw.get("creationDate", ""),
                    "modified": raw.get("modDate", ""),
                    "pages":    doc.page_count,
                }
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
        return meta

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def _hash_file(path: Path) -> str:
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()
