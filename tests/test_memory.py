import time
import pytest
from src.memory import InMemoryStore, SQLiteStore, create_memory_backend

@pytest.fixture
def in_memory():
    return InMemoryStore(ttl=1)

@pytest.fixture
def sqlite_memory():
    return SQLiteStore(db_path=":memory:", ttl=1)

def test_in_memory_add_and_get(in_memory):
    in_memory.add("user", "Hello")
    in_memory.add("assistant", "Hi there")
    recent = in_memory.get_recent(limit=2)
    assert len(recent) == 2
    assert recent[0]["role"] == "user"
    assert recent[0]["content"] == "Hello"
    assert recent[1]["role"] == "assistant"
    assert recent[1]["content"] == "Hi there"

def test_in_memory_ttl(in_memory):
    in_memory.add("user", "Hello")
    time.sleep(1.1)
    recent = in_memory.get_recent(limit=10)
    assert len(recent) == 0

def test_in_memory_clear(in_memory):
    in_memory.add("user", "Hello")
    in_memory.clear()
    assert len(in_memory.get_recent()) == 0

def test_sqlite_add_and_get(sqlite_memory):
    sqlite_memory.add("user", "Hello")
    sqlite_memory.add("assistant", "Hi")
    recent = sqlite_memory.get_recent(limit=2)
    assert len(recent) == 2
    assert recent[0]["content"] == "Hello"
    assert recent[1]["content"] == "Hi"

def test_sqlite_clear(sqlite_memory):
    sqlite_memory.add("user", "Hello")
    sqlite_memory.clear()
    assert len(sqlite_memory.get_recent()) == 0

def test_create_memory_backend_factory():
    config = {"type": "in_memory", "ttl": 100}
    backend = create_memory_backend(config)
    assert isinstance(backend, InMemoryStore)
    assert backend.ttl == 100

    config = {"type": "sqlite", "db_path": ":memory:", "ttl": 200}
    backend = create_memory_backend(config)
    assert isinstance(backend, SQLiteStore)
    assert backend.ttl == 200
