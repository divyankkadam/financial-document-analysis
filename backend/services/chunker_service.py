import re
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

FINANCIAL_SECTION_PATTERNS = [
    r"(executive\s+summary)",
    r"(revenue|net\s+revenue|total\s+revenue)",
    r"(gross\s+profit|gross\s+margin)",
    r"(operating\s+(income|loss|expenses))",
    r"(net\s+(income|loss|profit))",
    r"(earnings\s+per\s+share|eps)",
    r"(cash\s+flow)",
    r"(balance\s+sheet)",
    r"(risk\s+factors?)",
    r"(management.{0,20}discussion)",
    r"(forward.looking\s+statements?)",
    r"(segment\s+(results?|performance|overview))",
    r"(debt|liabilities|equity)",
    r"(dividend)",
    r"(outlook|guidance|forecast)",
]

_SECTION_RE = re.compile("|".join(FINANCIAL_SECTION_PATTERNS), re.IGNORECASE)


class ChunkerService:
    def __init__(self):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk(self, text: str, doc_id: str, file_name: str,
              doc_metadata: dict = None) -> list:
        doc_metadata = doc_metadata or {}
        sections     = self._split_into_sections(text)
        logger.info(f"Identified {len(sections)} sections in '{file_name}'")

        all_chunks  = []
        chunk_index = 0

        for section_name, section_text in sections:
            raw_chunks = self._splitter.split_text(section_text)
            for raw in raw_chunks:
                if not raw.strip():
                    continue
                page_num = self._infer_page_number(raw)
                doc = Document(
                    page_content=raw.strip(),
                    metadata={
                        "doc_id":      doc_id,
                        "file_name":   file_name,
                        "title":       doc_metadata.get("title", file_name),
                        "author":      doc_metadata.get("author", ""),
                        "section":     section_name,
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "char_count":  len(raw),
                    },
                )
                all_chunks.append(doc)
                chunk_index += 1

        logger.info(f"Chunked '{file_name}': {len(all_chunks)} chunks from {len(sections)} sections")
        return all_chunks

    def _split_into_sections(self, text: str) -> list:
        lines         = text.split("\n")
        sections      = []
        current_name  = "document"
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped and _SECTION_RE.search(stripped):
                if current_lines:
                    sections.append((current_name, "\n".join(current_lines)))
                current_name  = stripped[:80]
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_name, "\n".join(current_lines)))

        return sections if sections else [("document", text)]

    @staticmethod
    def _infer_page_number(text: str):
        match = re.search(r"\[Page (\d+)\]", text)
        return int(match.group(1)) if match else None
