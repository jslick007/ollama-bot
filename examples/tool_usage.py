"""
Demonstrates @tool decorator with various parameter types and the tool registry.
"""
from src.agent import Agent
from src.tool_executor import Tool, ToolRegistry

# Using Tool directly
def search_web(query: str, max_results: int = 5) -> str:
    return f"Search results for '{query}' (max: {max_results})"

search_tool = Tool(search_web)
print(f"Tool: {search_tool.name}")
print(f"Description: {search_tool.description}")
print(f"Parameters: {search_tool.definition.parameters}\n")

# Using ToolRegistry
registry = ToolRegistry()

@registry.register
def add(a: int, b: int) -> int:
    return a + b

@registry.register(name="concat", description="Concatenate two strings")
def join_strings(a: str, b: str) -> str:
    return a + b

print("Registered tools:", registry.list_tools())
print("Def 1:", registry.get("add").definition.name)
print("Def 2:", registry.get("concat").definition.name)
