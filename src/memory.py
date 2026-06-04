import time
import sqlite3
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryBackend(ABC):
    @abstractmethod
    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def clear(self):
        pass


class InMemoryStore(MemoryBackend):
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.messages = []

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        now = time.time()
        valid = [m for m in self.messages if now - m["timestamp"] < self.ttl]
        return valid[-limit:]

    def clear(self):
        self.messages = []


class SQLiteStore(MemoryBackend):
    def __init__(self, db_path: str = ":memory:", ttl: int = 3600):
        self.ttl = ttl
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY, role TEXT, content TEXT, timestamp REAL, metadata TEXT)")
        self.conn.commit()

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.conn.execute(
            "INSERT INTO memory (role, content, timestamp, metadata) VALUES (?, ?, ?, ?)",
            (role, content, time.time(), json.dumps(metadata or {}))
        )
        self.conn.commit()

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        now = time.time()
        cursor = self.conn.execute(
            "SELECT role, content, timestamp, metadata FROM memory WHERE ? - timestamp < ? ORDER BY id DESC LIMIT ?",
            (now, self.ttl, limit)
        )
        return [
            {"role": row[0], "content": row[1], "timestamp": row[2], "metadata": json.loads(row[3])}
            for row in cursor.fetchall()
        ][::-1]

    def clear(self):
        self.conn.execute("DELETE FROM memory")
        self.conn.commit()


def create_memory_backend(config: Dict[str, Any]) -> MemoryBackend:
    backend_type = config.get("type", "in_memory")
    ttl = config.get("ttl", 3600)
    if backend_type == "sqlite":
        db_path = config.get("db_path", ":memory:")
        return SQLiteStore(db_path=db_path, ttl=ttl)
    return InMemoryStore(ttl=ttl)
