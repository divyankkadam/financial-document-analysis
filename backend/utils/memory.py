import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)
MAX_TURNS   = 10
TTL_SECONDS = 3600


@dataclass
class Turn:
    question:   str
    answer:     str
    confidence: float
    doc_id:     str
    timestamp:  float = field(default_factory=time.time)


@dataclass
class Session:
    session_id:  str
    doc_id:      str
    turns:       list = field(default_factory=list)
    created_at:  float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_turn(self, question, answer, confidence, doc_id):
        self.turns.append(Turn(question, answer, confidence, doc_id))
        if len(self.turns) > MAX_TURNS:
            self.turns = self.turns[-MAX_TURNS:]
        self.last_active = time.time()

    def is_expired(self):
        return (time.time() - self.last_active) > TTL_SECONDS

    def format_history(self, n: int = 3) -> str:
        recent = self.turns[-n:]
        if not recent:
            return "No prior conversation."
        lines = []
        for i, t in enumerate(recent, 1):
            lines.append(f"Q{i}: {t.question}")
            lines.append(f"A{i}: {t.answer[:300]}{'…' if len(t.answer) > 300 else ''}")
        return "\n".join(lines)


class MemoryStore:
    def __init__(self):
        self._sessions: dict = {}

    def get_or_create(self, session_id: str, doc_id: str) -> Session:
        self._evict_expired()
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id, doc_id=doc_id)
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def _evict_expired(self) -> None:
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]


memory_store = MemoryStore()
