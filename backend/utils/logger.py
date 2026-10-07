import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(log_dir: str = "logs") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))

    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/app.jsonl", maxBytes=10*1024*1024,
        backupCount=5, encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())

    query_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/queries.jsonl", maxBytes=10*1024*1024,
        backupCount=5, encoding="utf-8",
    )
    query_handler.setLevel(logging.INFO)
    query_handler.setFormatter(JSONFormatter())

    for name in [
        "backend.nodes.retriever_node", "backend.nodes.crag_node",
        "backend.nodes.selfrag_node",   "backend.nodes.reasoning_node",
        "backend.nodes.answer_node",    "backend.routers.query_router",
    ]:
        logging.getLogger(name).addHandler(query_handler)

    root.addHandler(console)
    root.addHandler(file_handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
