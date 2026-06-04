import pytest
from unittest.mock import MagicMock
from src.planner import ReActPlanner
from src.tool_executor import ToolRegistry

def test_final_answer_direct():
    registry = ToolRegistry()
    mock_llm = MagicMock(return_value="Final Answer: 42")
    planner = ReActPlanner(llm=mock_llm, tool_registry=registry)
    result = planner.run("What is 6 times 7?")
    assert result == "42"

def test_one_tool_call_then_answer():
    registry = ToolRegistry()
    @registry.register
    def add(a: int, b: int) -> int:
        return a + b
    responses = [
        "Thought: I need to add 2 and 3.\nAction: add\nAction Input: {\"a\": 2, \"b\": 3}",
        "Final Answer: 5"
    ]
    mock_llm = MagicMock(side_effect=responses)
    planner = ReActPlanner(llm=mock_llm, tool_registry=registry)
    result = planner.run("Add 2 and 3")
    assert result == "5"

def test_max_iterations():
    registry = ToolRegistry()
    mock_llm = MagicMock(return_value="Thought: thinking...\nAction: nonexistent\nAction Input: {}")
    planner = ReActPlanner(llm=mock_llm, tool_registry=registry, max_iterations=3, max_tool_errors=10)
    result = planner.run("do something")
    assert "Max iterations reached" in result

def test_tool_error_handling():
    registry = ToolRegistry()
    @registry.register
    def failing_tool() -> str:
        raise ValueError("Something went wrong")
    responses = [
        "Thought: Let me try\nAction: failing_tool\nAction Input: {}",
        "Final Answer: done"
    ]
    mock_llm = MagicMock(side_effect=responses)
    planner = ReActPlanner(llm=mock_llm, tool_registry=registry, max_tool_errors=2)
    result = planner.run("use tool")
    assert result == "done"
