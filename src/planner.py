import re
import json
from typing import Callable
from src.tool_executor import ToolRegistry


class ReActPlanner:
    # New helper to decide if external search is required
    def _needs_external(self, task: str) -> bool:
        """Ask the LLM whether the task can be answered using only internal knowledge.
        Returns True if a web search is needed.
        """
        # Build a minimal prompt where the model must answer YES or NO
        check_prompt = [
            {
                "role": "system",
                "content": "You are to decide whether the answer to the following user request can be fully answered using only your internal knowledge. Respond with only YES or NO.",
            },
            {"role": "user", "content": task},
        ]
        response = self.llm(check_prompt)
        # Extract YES/NO from response
        match = re.search(r"\b(YES|NO)\b", response, re.IGNORECASE)
        if match:
            return match.group(1).upper() == "NO"
        # Fallback: assume external info is needed if unclear
        return True

    # Existing methods unchanged
    def __init__(
        self,
        llm: Callable,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
        max_tool_errors: int = 3,
    ):
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
        # First, decide if we need to search the web
        if hasattr(self, "_needs_external") and self._needs_external(task):
            try:
                # Perform a single web search using the task as the query
                search_result = self.tool_registry.execute("search_web", query=task)
                # Add the observation to the message history so the LLM can use it
                system_observation = f"Observation: {search_result}"
            except Exception as e:
                system_observation = f"Observation: Error during web search: {e}"
            # Initialize messages with system prompt and include the observation
            system_prompt = self._build_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": system_observation},
                {"role": "user", "content": task},
            ]
        else:
            # No external search needed; start with standard system prompt
            system_prompt = self._build_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
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
                    messages.append(
                        {
                            "role": "system",
                            "content": f"Error: Invalid JSON in Action Input: {raw_input}. Please provide valid JSON.",
                        }
                    )
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
                messages.append(
                    {"role": "system", "content": f"Observation: {result_str}"}
                )
            else:
                messages.append(
                    {
                        "role": "system",
                        "content": "Error: Could not parse response. Use the specified format with Thought/Action/Action Input or Final Answer.",
                    }
                )
            iteration += 1
        return "Max iterations reached without final answer."
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
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
                    messages.append(
                        {
                            "role": "system",
                            "content": f"Error: Invalid JSON in Action Input: {raw_input}. Please provide valid JSON.",
                        }
                    )
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
                messages.append(
                    {"role": "system", "content": f"Observation: {result_str}"}
                )
            else:
                messages.append(
                    {
                        "role": "system",
                        "content": "Error: Could not parse response. Use the specified format with Thought/Action/Action Input or Final Answer.",
                    }
                )
            iteration += 1
        return "Max iterations reached without final answer."
