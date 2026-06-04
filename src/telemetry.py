import time
import json
from typing import Dict, Any, Optional


DEFAULT_PRICING = {
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
}


class TelemetryCollector:
    def __init__(
        self,
        pricing: Optional[Dict[str, Dict[str, float]]] = None,
        log_to_stdout: bool = True,
        log_file: Optional[str] = None,
    ):
        self.pricing = pricing or DEFAULT_PRICING
        self.calls = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.log_to_stdout = log_to_stdout
        self.log_file = log_file
        self._file_handle = None
        if log_file:
            self._file_handle = open(log_file, "a")

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost: Optional[float] = None,
    ):
        if cost is None:
            cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        call = {
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "cost": cost,
            "timestamp": time.time(),
        }
        self.calls.append(call)
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += cost
        line = json.dumps(call)
        if self.log_to_stdout:
            print(line)
        if self._file_handle:
            self._file_handle.write(line + "\n")
            self._file_handle.flush()

    def _estimate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        prices = self.pricing.get(model, {"input": 0.002, "output": 0.002})
        return (
            prompt_tokens / 1000 * prices["input"]
            + completion_tokens / 1000 * prices["output"]
        )

    def report(self) -> Dict[str, Any]:
        return {
            "total_calls": len(self.calls),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": round(self.total_cost, 6),
            "average_latency_ms": round(
                sum(c["latency_ms"] for c in self.calls) / len(self.calls), 2
            )
            if self.calls
            else 0,
        }

    def reset(self):
        self.calls.clear()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
