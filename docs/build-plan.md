# Build Plan

## Milestone 1: Core LLM Interface (Week 1)
- Create `llm.py` wrapper for OpenAI API with token counting.
- Implement retry logic with exponential backoff.
- Add streaming and non-streaming modes.
- Unit tests for wrapper.

## Milestone 2: Prompt Manager & Compression (Week 2)
- Design prompt template system (system, tools, memory, user).
- Implement compression strategies: truncation, summarization (using same LLM), selective tool inclusion.
- Add prompt caching (LRU) for repeated patterns.
- Unit tests for token budget enforcement.

## Milestone 3: Memory System (Week 2-3)
- Define `MemoryBackend` abstract base class.
- Implement in‑memory store (list with TTL).
- Implement SQLite-backed store.
- Provide factory to choose backend via config.
- Unit tests for each backend.

## Milestone 4: Tool Executor (Week 3)
- Create decorator `@tool` to register functions with JSON‑Schema auto‑generation (using pydantic or docstring parsing).
- Schema validation of inputs before execution.
- Sandboxed execution (optional) via `restrictedpython` or simple allow‑list.
- Unit tests for registration, validation, and execution.

## Milestone 5: Planner / Reasoning Loop (Week 4)
- Implement ReAct loop: parse LLM output for `Thought:`, `Action:`, `Action Input:`.
- Configurable max iterations and stopping conditions (e.g., when `Final Answer:` appears).
- Integration with Tool Executor and Prompt Manager.
- Unit tests for end‑to‑end simple tasks.

## Milestone 6: Self‑Reflection Module (Week 5)
- After each loop, optionally call LLM to critique and suggest improvements.
- Integrate critiques back into prompt for another pass or to refine final answer.
- Toggle via config.
- Unit tests demonstrating quality improvement.

## Milestone 7: Observability & Telemetry (Week 5)
- Token counters per LLM call, cumulative per run.
- Cost estimator using model‑specific pricing (loaded from config).
- Latency tracking (start/end timestamps).
- Structured logging (JSON) to file/stdout.
- Export metrics (Prometheus optional).

## Milestone 8: Agent Orchestrator & API (Week 6)
- Public class `Agent` with `__init__(config)` and `run(task)`, `async_run(task)`.
- Simple YAML config loader.
- Provide example scripts and CLI entry point.
- Documentation strings and type hints.

## Milestone 9: Packaging & Distribution (Week 7)
- Write `pyproject.toml`, `setup.cfg`, README.
- Create Dockerfile (base: python:3.11-slim).
- GitHub Actions CI: lint, test, build wheel.
- Publish to TestPyPI then PyPI.

## Milestone 10: Documentation & Examples (Week 8)
- Write tutorials: basic agent, tool usage, memory persistence, self‑reflection.
- Example: web search agent using a hypothetical search tool.
- Example: multi‑agent coordination (two agents delegating subtasks).
- Generate API reference (mkdocstrings).

## Risk & Mitigation
- **Risk**: LLM output parsing failures.
  **Mitigation**: Use structured output (JSON mode) if supported; fallback to regex with reparsing prompts.
- **Risk**: Token budget exceeded despite compression.
  **Mitigation**: Dynamic compression escalation (truncate → summarize → drop oldest).
- **Risk**: Tool execution errors causing loop stuck.
  **Mitigation**: Maximum tool error count; return error observation to LLM.
- **Risk**: Latency too high for interactive use.
  **Mitigation**: Streaming responses, async support, model selection (e.g., gpt-3.5-turbo).

## Dependencies
- openai>=1.0.0
- pydantic (for schema)
- PyYAML
- tinydb or sqlite3 (built‑in)
- pytest, pytest-asyncio
- (optional) redis, tiktoken

## Timeline Summary
| Week | Focus |
|------|-------|
| 1 | LLM wrapper |
| 2 | Prompt manager + memory |
| 3 | Tool executor + memory backends |
| 4 | Reasoning loop |
| 5 | Self‑reflection + observability |
| 6 | Agent orchestrator |
| 7 | Packaging & CI |
| 8 | Documentation & examples |
