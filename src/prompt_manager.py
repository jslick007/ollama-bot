from collections import OrderedDict
from typing import List, Dict, Any, Optional, Callable


class PromptTemplate:
    def __init__(self, system: str = "", tools: str = "", memory: str = "", user: str = ""):
        self.system = system
        self.tools = tools
        self.memory = memory
        self.user = user

    def build(self, system: Optional[str] = None, tools: Optional[str] = None,
              memory: Optional[str] = None, user: Optional[str] = None) -> List[Dict[str, str]]:
        messages = []
        sys_content = system if system is not None else self.system
        if sys_content:
            messages.append({"role": "system", "content": sys_content})
        tools_content = tools if tools is not None else self.tools
        memory_content = memory if memory is not None else self.memory
        combined_context = ""
        if tools_content:
            combined_context += f"Tools available:\n{tools_content}\n"
        if memory_content:
            combined_context += f"Memory:\n{memory_content}\n"
        if combined_context:
            messages.append({"role": "system", "content": combined_context.strip()})
        user_content = user if user is not None else self.user
        if user_content:
            messages.append({"role": "user", "content": user_content})
        return messages


class PromptCache:
    def __init__(self, capacity: int = 100):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[List[Dict[str, str]]]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: List[Dict[str, str]]):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()


class CompressionStrategy:
    def __init__(self, token_counter: Callable[[str], int], max_tokens: int = 4096):
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def truncate(self, messages: List[Dict[str, str]], reserve: int = 512) -> List[Dict[str, str]]:
        budget = self.max_tokens - reserve
        result = []
        total = 0
        for msg in messages:
            tokens = self.token_counter(msg["content"])
            remaining = budget - total
            if tokens <= remaining:
                result.append(msg)
                total += tokens
            else:
                truncated = msg["content"][:remaining]
                result.append({"role": msg["role"], "content": truncated})
                total += remaining
                break
        return result

    def summarize(self, messages: List[Dict[str, str]],
                  llm: Callable[[List[Dict[str, str]]], str]) -> List[Dict[str, str]]:
        full_text = "\n".join(m["content"] for m in messages)
        tokens = self.token_counter(full_text)
        if tokens <= self.max_tokens:
            return messages
        summarization_prompt = [
            {"role": "system", "content": "Summarize the following conversation concisely, preserving key facts and context."},
            {"role": "user", "content": full_text}
        ]
        summary = llm(summarization_prompt)
        budget = self.max_tokens // 2
        if self.token_counter(summary) > budget:
            summary = summary[:budget]
        return [{"role": "system", "content": f"Summary of previous conversation:\n{summary}"}]

    def select_tools(self, tools: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        scored = []
        for tool in tools:
            desc = tool.get("description", "").lower()
            name = tool.get("name", "").lower()
            score = 0
            for word in query_lower.split():
                if word in desc or word in name:
                    score += 1
            scored.append((score, tool))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored if _ > 0] or tools[:3]
