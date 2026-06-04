"""
Basic agent example demonstrating tool registration and task execution.
"""

from src.agent import Agent

agent = Agent(config={"llm": {"api_key": "your-api-key-here"}})


@agent.register_tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@agent.register_tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


result = agent.run("What is 123 * 456?")
print(f"Result: {result}")
print(f"Report: {agent.report()}")
