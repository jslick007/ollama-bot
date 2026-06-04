"""
Demonstrates using SQLite-backed memory for conversation persistence.
"""

from src.memory import SQLiteStore

memory = SQLiteStore(db_path=":memory:", ttl=3600)

# Simulate a conversation
memory.add("user", "Hello, my name is Alice")
memory.add("assistant", "Hi Alice! How can I help you?")
memory.add("user", "What's the weather like?")
memory.add("assistant", "I don't have access to weather data.")

# Retrieve recent context
recent = memory.get_recent(limit=4)
for msg in recent:
    print(f"{msg['role']}: {msg['content']}")

memory.clear()
print(f"\nMessages after clear: {len(memory.get_recent())}")
