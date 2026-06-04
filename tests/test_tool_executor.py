import pytest
from pydantic import ValidationError
from src.tool_executor import Tool, ToolRegistry

def test_tool_definition():
    def add(a: int, b: int) -> int:
        return a + b
    tool = Tool(add)
    assert tool.name == "add"
    assert tool.definition.parameters["properties"]["a"]["type"] == "int"

def test_tool_execute():
    def add(a: int, b: int = 0) -> int:
        return a + b
    tool = Tool(add)
    result = tool.execute(a=3, b=4)
    assert result == 7

def test_tool_validation():
    def greet(name: str) -> str:
        return f"Hello {name}"
    tool = Tool(greet)
    with pytest.raises(ValidationError):
        tool.execute(name=123)

def test_registry():
    registry = ToolRegistry()
    @registry.register
    def add(a: int, b: int) -> int:
        return a + b
    assert registry.get("add") is not None
    assert registry.list_tools() == ["add"]
    assert len(registry.definitions()) == 1

def test_registry_execute():
    registry = ToolRegistry()
    @registry.register
    def multiply(a: int, b: int) -> int:
        return a * b
    result = registry.execute("multiply", a=3, b=4)
    assert result == 12

def test_unknown_tool():
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.execute("nonexistent")

def test_allowlist():
    registry = ToolRegistry(allowlist=["add"])
    @registry.register
    def add(a: int, b: int) -> int:
        return a + b
    @registry.register
    def subtract(a: int, b: int) -> int:
        return a - b
    result = registry.execute("add", a=1, b=2)
    assert result == 3
    with pytest.raises(PermissionError):
        registry.execute("subtract", a=5, b=3)
