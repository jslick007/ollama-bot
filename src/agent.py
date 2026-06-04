import time
import asyncio
from typing import Any, Dict, List, Optional
from src.llm import OpenAILLM
from src.tool_executor import ToolRegistry
from src.planner import ReActPlanner
from src.memory import create_memory_backend, MemoryBackend
from src.self_reflection import SelfReflectionModule
from src.telemetry import TelemetryCollector
from src.config import load_config
from src.tools import search_web


class Agent:
    def __init__(
        self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None
    ):
        self.config = load_config(path=config_path, overrides=config)
        self.llm = self._init_llm()
        self.tool_registry = ToolRegistry()
        self.memory = self._init_memory()
        self.telemetry = TelemetryCollector(
            log_to_stdout=self.config.get("telemetry", {}).get("log_to_stdout", True),
            log_file=self.config.get("telemetry", {}).get("log_file"),
        )
        self.reflection = SelfReflectionModule(
            llm=self._llm_call,
            enabled=self.config.get("self_reflection", {}).get("enabled", False),
        )
        self.planner = ReActPlanner(
            llm=self._llm_call_with_telemetry,
            tool_registry=self.tool_registry,
            max_iterations=self.config.get("planner", {}).get("max_iterations", 10),
            max_tool_errors=self.config.get("planner", {}).get("max_tool_errors", 3),
        )
        self._register_default_tools()

    def _init_llm(self) -> OpenAILLM:
        llm_config = self.config.get("llm", {})
        return OpenAILLM(
            api_key=llm_config.get("api_key", ""),
            base_url=llm_config.get("base_url"),
            model=llm_config.get("model", "tinyllama:latest"),
        )

    def _init_memory(self) -> MemoryBackend:
        return create_memory_backend(self.config.get("memory", {}))

    def _llm_call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return self.llm.generate(messages, **kwargs)

    def _llm_call_with_telemetry(self, messages: List[Dict[str, str]], **kwargs) -> str:
        start = time.time()
        result = self._llm_call(messages, **kwargs)
        elapsed = (time.time() - start) * 1000
        prompt_text = "\n".join(m.get("content", "") for m in messages)
        prompt_tokens = self.llm.count_tokens(prompt_text)
        completion_tokens = self.llm.count_tokens(result)
        self.telemetry.record_llm_call(
            model=self.llm.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=elapsed,
        )
        return result

    def _register_default_tools(self):
        self.tool_registry.register(
            search_web,
            name="search_web",
            description="Search the web for information using DuckDuckGo. Returns titles, snippets, and source URLs.",
        )
        # Register a simple page‑fetcher so the planner can retrieve full page content.
        from src.tools.web_fetch import fetch_page

        self.tool_registry.register(
            fetch_page,
            name="fetch_page",
            description="Fetch the raw HTML/text of a URL (used to get full page content after a search).",
        )

    def register_tool(
        self, fn=None, *, name: Optional[str] = None, description: Optional[str] = None
    ):
        if name is not None:
            return self.tool_registry.register(fn, name=name, description=description)
        return self.tool_registry.register(fn, name=name, description=description)

    def run(self, task: str) -> str:
        return self.planner.run(task)

    async def async_run(self, task: str) -> str:
        return await asyncio.to_thread(self.run, task)

    def report(self) -> Dict[str, Any]:
        return self.telemetry.report()
