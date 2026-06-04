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
            "Final Answer:\n"
            "Search query: <exact DDG query 1>\n"
            "Search query: <exact DDG query 2>\n"
            "\n"
            "| Issue | Recommendation |\n"
            "|-------|----------------|\n"
            "| …     | …              |\n"
            "\n"
            "You **must** output exactly as shown—no introductory sentences, no extra commentary, and no repetition of the user question.\n"
            "Do NOT echo the original user query, any 'search:' headings, or repeat the question in the answer. Only output the requested search queries and table."
        )

    # Helper to extract 3‑4 concise search terms from the user task
    def _extract_search_terms(self, task: str) -> list:
        """Ask the LLM to return a JSON list of 3‑4 short terms that capture the intent."""
        prompt = [
            {
                "role": "system",
                "content": 'You are to extract a short list of 3‑4 key search terms that best represent the user request. Return a JSON array of strings, e.g., ["term1", "term2"].',
            },
            {"role": "user", "content": task},
        ]
        response = self.llm(prompt)
        try:
            terms = json.loads(response)
            if isinstance(terms, list) and all(isinstance(t, str) for t in terms):
                return terms[:4]
        except json.JSONDecodeError:
            pass
        # Fallback: split task into words and take first few unique words
        return list(dict.fromkeys(task.split()))[:4]

    # Helper to verify the generated answer against the original intent
    def _verify_answer(self, task: str, answer: str) -> bool:
        """Ask the LLM if the answer fully satisfies the original request. Returns True for YES."""
        verify_prompt = [
            {
                "role": "system",
                "content": "Given the original user request and a proposed answer, decide if the answer completely satisfies the request. Respond with only YES or NO.",
            },
            {"role": "user", "content": f"Request: {task}\nAnswer: {answer}"},
        ]
        response = self.llm(verify_prompt)
        match = re.search(r"\b(YES|NO)\b", response, re.IGNORECASE)
        if match:
            return match.group(1).upper() == "YES"
        return False

    def run(self, task: str) -> str:
        # 1️⃣  Quick external‑info check (single LLM call)
        need_external = hasattr(self, "_needs_external") and self._needs_external(task)
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        if need_external:
            # 2️⃣  Extract up to two concise search terms (single LLM call inside _extract_search_terms)
            terms = self._extract_search_terms(task)[:2]
            for term in terms:
                try:
                    # One DDG request per term – add the exact query to the context
                    result = self.tool_registry.execute("search_web", query=term)
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"Observation: Query: {term}\n{result}",
                        }
                    )
                    # Extract any source URLs from the DDG result and fetch their full content
                    for url in re.findall(r"Source:\s*(\S+)", result):
                        try:
                            page_content = self.tool_registry.execute(
                                "fetch_page", url=url
                            )
                            # Include only a preview to keep token usage reasonable
                            preview = page_content[:2000]
                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": f"Page content from {url}:\n{preview}",
                                }
                            )
                        except Exception:
                            # If fetching fails, continue without aborting the flow
                            continue
                except Exception:
                    # If a search fails, just continue – we still want a fast answer
                    continue

        # 3️⃣  Append the original user request and get the final answer in ONE LLM call
        messages.append({"role": "user", "content": task})
        answer_response = self.llm(messages)
        # Respect the "Final Answer:" wrapper if the model uses it
        final_match = re.search(r"Final Answer:\s*(.*)", answer_response, re.DOTALL)
        answer = (
            final_match.group(1).strip() if final_match else answer_response.strip()
        )

        # 4️⃣  OPTIONAL verification – disabled for speed. Uncomment if you need strictness.
        # if need_external:
        #     if not self._verify_answer(task, answer):
        #         return "Unable to verify that the generated answer fully satisfies the user intent."
        return answer
