import logging
import re
from functools import lru_cache

from langchain_core.documents import Document
from neo4j import GraphDatabase

from app.config import settings
from services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

CHUNK_VECTOR_INDEX = "chunk_embedding_index"

_METRIC_ALIASES = {
    "revenue": "Revenue",
    "net revenue": "Net Revenue",
    "total revenue": "Total Revenue",
    "gross profit": "Gross Profit",
    "gross margin": "Gross Margin",
    "operating income": "Operating Income",
    "operating loss": "Operating Loss",
    "operating expenses": "Operating Expenses",
    "net income": "Net Income",
    "net loss": "Net Loss",
    "net profit": "Net Profit",
    "earnings per share": "Earnings Per Share",
    "eps": "Earnings Per Share",
    "cash flow": "Cash Flow",
    "assets": "Assets",
    "liabilities": "Liabilities",
    "equity": "Equity",
}

_METRIC_RE = re.compile(
    r"\b("
    + "|".join(re.escape(k) for k in sorted(_METRIC_ALIASES, key=len, reverse=True))
    + r")\b"
    r"(?:[^.\n$%]{0,80})?"
    r"(?P<value>\(?[-+]?\$?\d[\d,]*(?:\.\d+)?\)?\s*(?:%|million|billion|m|bn)?)?",
    re.IGNORECASE,
)
_PERIOD_RE = re.compile(r"\b(Q[1-4]\s+20\d{2}|FY\s?20\d{2}|20\d{2})\b", re.IGNORECASE)
_STATEMENT_RE = re.compile(
    r"\b(balance sheet|income statement|statement of operations|cash flow statement|financial statement)\b",
    re.IGNORECASE,
)


class VectorStoreService:
    """
    Neo4j-backed Hybrid GraphRAG store. Stores a document/page/chunk graph and
    uses Neo4j vector search for retrieval.
    """

    def __init__(self):
        self._embeddings = None
        self._driver = None
        self._database = settings.neo4j_database or None
        self._schema_ready = False

    def add_documents(self, doc_id: str, documents: list[Document]) -> int:
        if not documents:
            logger.warning("add_documents called with empty list - skipping")
            return 0

        texts = [doc.page_content for doc in documents]
        vectors = self._get_embeddings().embed_documents(texts)
        rows = [
            {
                "chunk_id": self._chunk_id(doc_id, doc.metadata.get("chunk_index", i)),
                "doc_id": doc_id,
                "text": doc.page_content,
                "embedding": [float(v) for v in vectors[i]],
                "metadata": self._clean_props(doc.metadata),
                "metrics": self._extract_metric_mentions(doc.page_content),
                "periods": self._extract_periods(doc.page_content),
                "statements": self._extract_statements(doc.page_content, doc.metadata.get("section", "")),
            }
            for i, doc in enumerate(documents)
        ]

        self._execute_write(self._upsert_chunks, rows)
        total = self._execute_read(self._count_chunks, doc_id)
        logger.info(f"Graph index '{doc_id[:8]}...' now contains {total} chunks")
        return total

    def add_document_structure(self, parsed) -> None:
        """
        Persist document/page/table hierarchy so financial tables remain
        traversable even when text chunks split nearby narrative content.
        """
        doc = {
            "doc_id": parsed.doc_id,
            "file_name": parsed.file_name,
            "file_path": parsed.file_path,
            "total_pages": parsed.total_pages,
            "metadata": self._clean_props(parsed.doc_metadata),
        }
        pages = []
        tables = []
        cells = []
        for page in parsed.pages:
            page_id = f"{parsed.doc_id}:p:{page.page_number}"
            pages.append(
                {
                    "page_id": page_id,
                    "doc_id": parsed.doc_id,
                    "page_number": page.page_number,
                    "text": page.text,
                }
            )
            for table_index, table in enumerate(page.tables or []):
                table_id = f"{page_id}:t:{table_index}"
                tables.append(
                    {
                        "table_id": table_id,
                        "page_id": page_id,
                        "doc_id": parsed.doc_id,
                        "table_index": table_index,
                    }
                )
                for row_index, row in enumerate(table or []):
                    row_id = f"{table_id}:r:{row_index}"
                    for col_index, value in enumerate(row or []):
                        cells.append(
                            {
                                "cell_id": f"{row_id}:c:{col_index}",
                                "row_id": row_id,
                                "table_id": table_id,
                                "doc_id": parsed.doc_id,
                                "row_index": row_index,
                                "col_index": col_index,
                                "value": "" if value is None else str(value).strip(),
                            }
                        )

        self._execute_write(self._upsert_document_structure, doc, pages, tables, cells)
        logger.info(
            f"Stored graph structure for '{parsed.file_name}': "
            f"{len(pages)} pages, {len(tables)} tables, {len(cells)} cells"
        )

    def search(self, doc_id: str, query: str, k: int = 6, score_threshold: float = 0.0) -> list:
        if not self._index_exists(doc_id):
            logger.warning(f"search: no graph chunks found for doc_id='{doc_id[:8]}...'")
            return []

        query_vector = [float(v) for v in self._get_embeddings().embed_query(query)]
        rows = self._execute_read(
            self._vector_search,
            doc_id,
            query_vector,
            k,
            max(score_threshold, 0.0),
        )
        results = [
            (
                Document(
                    page_content=row["text"],
                    metadata={k: v for k, v in row["metadata"].items() if k != "embedding"},
                ),
                float(1.0 - row["score"]),
            )
            for row in rows
        ]
        logger.info(f"search: doc='{doc_id[:8]}...' -> {len(results)}/{k} results")
        return results

    def search_documents(self, doc_id: str, query: str, k: int = 6) -> list:
        return [doc for doc, _ in self.search(doc_id, query, k)]

    def delete(self, doc_id: str) -> bool:
        deleted = self._execute_write(self._delete_doc, doc_id)
        if deleted:
            logger.info(f"Deleted graph index for doc_id='{doc_id[:8]}...'")
        return bool(deleted)

    def list_indexes(self) -> list:
        return self._execute_read(self._list_doc_ids)

    def get_index_stats(self, doc_id: str) -> dict:
        stats = self._execute_read(self._stats, doc_id)
        if not stats or stats["total_chunks"] == 0:
            return {"exists": False}
        return {
            "exists": True,
            "doc_id": doc_id,
            "provider": "neo4j",
            "vector_index": CHUNK_VECTOR_INDEX,
            "total_vectors": stats["total_chunks"],
            "total_pages": stats["total_pages"],
            "total_tables": stats["total_tables"],
            "total_table_cells": stats["total_cells"],
            "total_metrics": stats["total_metrics"],
        }

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._get_driver().session(database=self._database) as session:
            session.run("CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE")
            session.run("CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.page_id IS UNIQUE")
            session.run("CREATE CONSTRAINT section_key IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE")
            session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE")
            session.run("CREATE CONSTRAINT metric_key IF NOT EXISTS FOR (m:Metric) REQUIRE m.metric_id IS UNIQUE")
            session.run("CREATE CONSTRAINT period_key IF NOT EXISTS FOR (p:Period) REQUIRE p.period_id IS UNIQUE")
            session.run("CREATE CONSTRAINT statement_key IF NOT EXISTS FOR (s:Statement) REQUIRE s.statement_id IS UNIQUE")
            session.run("CREATE CONSTRAINT table_id IF NOT EXISTS FOR (t:FinancialTable) REQUIRE t.table_id IS UNIQUE")
            session.run("CREATE CONSTRAINT row_id IF NOT EXISTS FOR (r:TableRow) REQUIRE r.row_id IS UNIQUE")
            session.run("CREATE CONSTRAINT cell_id IF NOT EXISTS FOR (c:TableCell) REQUIRE c.cell_id IS UNIQUE")
            session.run(
                f"""
                CREATE VECTOR INDEX {CHUNK_VECTOR_INDEX} IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {{indexConfig: {{
                    `vector.dimensions`: {settings.embedding_dimension},
                    `vector.similarity_function`: 'cosine'
                }}}}
                """
            )
        self._schema_ready = True

    def _get_driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        return self._driver

    def _get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embedding_service()
        return self._embeddings

    def _execute_read(self, fn, *args):
        self._ensure_schema()
        with self._get_driver().session(database=self._database) as session:
            return session.execute_read(fn, *args)

    def _execute_write(self, fn, *args):
        self._ensure_schema()
        with self._get_driver().session(database=self._database) as session:
            return session.execute_write(fn, *args)

    @staticmethod
    def _upsert_document_structure(tx, doc, pages, tables, cells) -> None:
        tx.run(
            """
            MERGE (d:Document {doc_id: $doc.doc_id})
            SET d.file_name = $doc.file_name,
                d.file_path = $doc.file_path,
                d.total_pages = $doc.total_pages,
                d += $doc.metadata
            """,
            doc=doc,
        )
        tx.run(
            """
            UNWIND $pages AS page
            MATCH (d:Document {doc_id: page.doc_id})
            MERGE (p:Page {page_id: page.page_id})
            SET p.doc_id = page.doc_id,
                p.page_number = page.page_number,
                p.text = page.text
            MERGE (d)-[:HAS_PAGE]->(p)
            """,
            pages=pages,
        )
        tx.run(
            """
            UNWIND $tables AS table
            MATCH (p:Page {page_id: table.page_id})
            MERGE (t:FinancialTable {table_id: table.table_id})
            SET t.doc_id = table.doc_id,
                t.table_index = table.table_index
            MERGE (p)-[:HAS_TABLE]->(t)
            """,
            tables=tables,
        )
        tx.run(
            """
            UNWIND $cells AS cell
            MATCH (t:FinancialTable {table_id: cell.table_id})
            MERGE (r:TableRow {row_id: cell.row_id})
            SET r.doc_id = cell.doc_id,
                r.row_index = cell.row_index
            MERGE (t)-[:HAS_ROW]->(r)
            MERGE (c:TableCell {cell_id: cell.cell_id})
            SET c.doc_id = cell.doc_id,
                c.row_index = cell.row_index,
                c.col_index = cell.col_index,
                c.value = cell.value
            MERGE (r)-[:HAS_CELL]->(c)
            """,
            cells=cells,
        )

    @staticmethod
    def _upsert_chunks(tx, rows) -> None:
        tx.run(
            """
            UNWIND $rows AS row
            MERGE (d:Document {doc_id: row.doc_id})
            ON CREATE SET d.file_name = row.metadata.file_name
            MERGE (s:Section {section_id: row.doc_id + ':' + row.metadata.section})
            SET s.doc_id = row.doc_id,
                s.name = row.metadata.section
            MERGE (d)-[:HAS_SECTION]->(s)
            MERGE (c:Chunk {chunk_id: row.chunk_id})
            SET c.doc_id = row.doc_id,
                c.text = row.text,
                c.embedding = row.embedding,
                c.file_name = row.metadata.file_name,
                c.title = row.metadata.title,
                c.section = row.metadata.section,
                c.chunk_index = row.metadata.chunk_index,
                c.page_number = row.metadata.page_number,
                c.char_count = row.metadata.char_count
            MERGE (s)-[:HAS_CHUNK]->(c)
            WITH row, d, s, c
            OPTIONAL MATCH (p:Page {doc_id: row.doc_id, page_number: row.metadata.page_number})
            FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | MERGE (p)-[:HAS_CHUNK]->(c))
            WITH row, d, s, c
            UNWIND row.metrics AS metric
            MERGE (m:Metric {metric_id: row.doc_id + ':' + metric.name})
            SET m.doc_id = row.doc_id,
                m.name = metric.name,
                m.latest_value = metric.value
            MERGE (m)-[:REPORTED_IN]->(d)
            MERGE (m)-[:MENTIONED_IN]->(c)
            WITH row, d, s, c
            UNWIND row.periods AS period
            MERGE (p:Period {period_id: row.doc_id + ':' + period})
            SET p.doc_id = row.doc_id,
                p.label = period
            MERGE (c)-[:FOR_PERIOD]->(p)
            WITH row, d, s, c
            UNWIND row.statements AS statement
            MERGE (fs:Statement {statement_id: row.doc_id + ':' + statement})
            SET fs.doc_id = row.doc_id,
                fs.name = statement
            MERGE (fs)-[:REPORTED_IN]->(d)
            MERGE (c)-[:PART_OF_STATEMENT]->(fs)
            """,
            rows=rows,
        )

    @staticmethod
    def _vector_search(tx, doc_id, query_vector, k, score_threshold) -> list:
        fetch_k = max(k * 10, 50)
        result = tx.run(
            f"""
            CALL db.index.vector.queryNodes('{CHUNK_VECTOR_INDEX}', $fetch_k, $query_vector)
            YIELD node, score
            WHERE node.doc_id = $doc_id AND score >= $score_threshold
            RETURN node.text AS text,
                   score,
                   properties(node) AS metadata
            ORDER BY score DESC
            LIMIT $k
            """,
            doc_id=doc_id,
            query_vector=query_vector,
            fetch_k=fetch_k,
            k=k,
            score_threshold=score_threshold,
        )
        return [dict(record) for record in result]

    @staticmethod
    def _count_chunks(tx, doc_id) -> int:
        record = tx.run(
            "MATCH (c:Chunk {doc_id: $doc_id}) RETURN count(c) AS total",
            doc_id=doc_id,
        ).single()
        return int(record["total"]) if record else 0

    @staticmethod
    def _index_exists_tx(tx, doc_id) -> bool:
        record = tx.run(
            "MATCH (c:Chunk {doc_id: $doc_id}) RETURN count(c) > 0 AS exists",
            doc_id=doc_id,
        ).single()
        return bool(record["exists"]) if record else False

    def _index_exists(self, doc_id: str) -> bool:
        return self._execute_read(self.__class__._index_exists_tx, doc_id)

    @staticmethod
    def _delete_doc(tx, doc_id) -> int:
        result = tx.run(
            """
            MATCH (n {doc_id: $doc_id})
            DETACH DELETE n
            RETURN count(n) AS deleted
            """,
            doc_id=doc_id,
        )
        record = result.single()
        return int(record["deleted"]) if record else 0

    @staticmethod
    def _list_doc_ids(tx) -> list:
        result = tx.run(
            """
            MATCH (d:Document)
            WHERE EXISTS {
                MATCH (d)-[:HAS_SECTION]->(:Section)-[:HAS_CHUNK]->(:Chunk)
            }
            RETURN d.doc_id AS doc_id
            ORDER BY d.file_name, d.doc_id
            """
        )
        return [record["doc_id"] for record in result]

    @staticmethod
    def _stats(tx, doc_id) -> dict:
        record = tx.run(
            """
            MATCH (d:Document {doc_id: $doc_id})
            OPTIONAL MATCH (d)-[:HAS_SECTION]->(:Section)-[:HAS_CHUNK]->(c:Chunk)
            WITH d, count(DISTINCT c) AS total_chunks
            OPTIONAL MATCH (d)-[:HAS_PAGE]->(p:Page)
            WITH d, total_chunks, count(DISTINCT p) AS total_pages
            OPTIONAL MATCH (d)-[:HAS_PAGE]->(:Page)-[:HAS_TABLE]->(t:FinancialTable)
            WITH d, total_chunks, total_pages, count(DISTINCT t) AS total_tables
            OPTIONAL MATCH (d)-[:HAS_PAGE]->(:Page)-[:HAS_TABLE]->(:FinancialTable)-[:HAS_ROW]->(:TableRow)-[:HAS_CELL]->(cell:TableCell)
            WITH d, total_chunks, total_pages, total_tables, count(DISTINCT cell) AS total_cells
            OPTIONAL MATCH (m:Metric {doc_id: $doc_id})-[:REPORTED_IN]->(d)
            RETURN total_chunks, total_pages, total_tables, total_cells, count(DISTINCT m) AS total_metrics
            """,
            doc_id=doc_id,
        ).single()
        return dict(record) if record else {}

    @staticmethod
    def _chunk_id(doc_id: str, chunk_index) -> str:
        return f"{doc_id}:chunk:{chunk_index}"

    @staticmethod
    def _clean_props(props: dict) -> dict:
        clean = {}
        for key, value in (props or {}).items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                clean[key] = str(value)
        return clean

    @staticmethod
    def _extract_periods(text: str) -> list[str]:
        return sorted({match.group(1).upper().replace("FY ", "FY") for match in _PERIOD_RE.finditer(text or "")})

    @staticmethod
    def _extract_statements(text: str, section: str = "") -> list[str]:
        haystack = f"{section}\n{text or ''}"
        return sorted({match.group(1).title() for match in _STATEMENT_RE.finditer(haystack)})

    @staticmethod
    def _extract_metric_mentions(text: str) -> list[dict]:
        mentions = []
        seen = set()
        for match in _METRIC_RE.finditer(text or ""):
            raw_name = match.group(1).lower()
            name = _METRIC_ALIASES.get(raw_name, raw_name.title())
            value = (match.group("value") or "").strip()
            key = (name, value)
            if key in seen:
                continue
            seen.add(key)
            mentions.append({"name": name, "value": value})
        return mentions


@lru_cache(maxsize=1)
def get_vectorstore_service() -> VectorStoreService:
    return VectorStoreService()
