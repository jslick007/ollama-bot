import re
import json
from typing import List, Dict, Any, Optional, Callable
from src.tool_executor import ToolRegistry, ToolDefinition
from src.prompt_manager import PromptTemplate


class ReActPlanner:
    def __init__(self, llm: Callable, tool_registry: ToolRegistry,
                 max_iterations: int = 10, max_tool_errors: int = 3):
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.max_tool_errors = max_tool_errors
        self.tool_errors = 0

    def _build_system_prompt(self) -> str:
        tools_desc = "\n".join(
            f"- {t.name}: {t.description} (parameters: {json.dumps(t.parameters, default=str)})"
            for t in self.tool_registry.definitions()
        )
        return (
            "You are a helpful AI agent. You can use the following tools to accomplish tasks.\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            "You must respond in the following format:\n"
            "Thought: <your reasoning>\n"
            "Action: <tool name>\n"
            "Action Input: <JSON arguments>\n"
            "or if you have the final answer:\n"
            "Final Answer: <answer>"
        )

    def run(self, task: str) -> str:
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]
        iteration = 0
        while iteration < self.max_iterations:
            response = self.llm(messages)
            messages.append({"role": "assistant", "content": response})
            final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
            if final_match:
                return final_match.group(1).strip()
            action_match = re.search(r"Action:\s*(\w+)", response)
            input_match = re.search(r"Action Input:\s*(.*)", response, re.DOTALL)
            if action_match and input_match:
                action = action_match.group(1)
                raw_input = input_match.group(1).strip()
                try:
                    action_input = json.loads(raw_input)
                except json.JSONDecodeError:
                    messages.append({"role": "system", "content": f"Error: Invalid JSON in Action Input: {raw_input}. Please provide valid JSON."})
                    continue
                try:
                    result = self.tool_registry.execute(action, **action_input)
                    result_str = str(result)
                    self.tool_errors = 0
                except (ValueError, PermissionError, Exception) as e:
                    self.tool_errors += 1
                    if self.tool_errors >= self.max_tool_errors:
                        return f"Task failed after {self.tool_errors} tool errors."
                    result_str = f"Error: {str(e)}"
                messages.append({"role": "system", "content": f"Observation: {result_str}"})
            else:
                messages.append({"role": "system", "content": "Error: Could not parse response. Use the specified format with Thought/Action/Action Input or Final Answer."})
            iteration += 1
        return "Max iterations reached without final answer."
