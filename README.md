# Ollama Bot

A lightweight, token-efficient AI agent harness for building agents that can reason, act, and learn within tight cost and latency constraints.

## Quick Start

```python
from src.agent import Agent

agent = Agent(config={"llm": {"api_key": "your-key"}})

@agent.register_tool
def search(query: str) -> str:
    return f"Results for {query}"

result = agent.run("Find information about Python")
print(result)
print(agent.report())
```

## Configuration

See `docs/` for full documentation.
