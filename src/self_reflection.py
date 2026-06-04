from typing import List, Dict, Optional, Callable


class SelfReflectionModule:
    def __init__(self, llm: Callable, enabled: bool = False):
        self.llm = llm
        self.enabled = enabled

    def critique(self, conversation: List[Dict[str, str]]) -> Optional[str]:
        if not self.enabled:
            return None
        history = "\n".join(f"{m['role']}: {m['content']}" for m in conversation)
        critique_prompt = [
            {
                "role": "system",
                "content": "You are a critic reviewing an AI agent's reasoning. Identify flaws, suggest improvements, and note any missing steps.",
            },
            {"role": "user", "content": f"Review this conversation:\n{history}"},
        ]
        return self.llm(critique_prompt)

    def refine(self, original_response: str, critique: str) -> str:
        if not self.enabled or not critique:
            return original_response
        refine_prompt = [
            {
                "role": "system",
                "content": "Improve the following answer based on the critique provided.",
            },
            {
                "role": "user",
                "content": f"Original answer:\n{original_response}\n\nCritique:\n{critique}\n\nProvide an improved final answer.",
            },
        ]
        return self.llm(refine_prompt)
