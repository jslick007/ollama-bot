# Architecture Overview

## High-Level Components
1. **LLM Interface** – Wrapper around OpenAI API (or compatible) handling token counting, retries, and streaming.
2. **Prompt Manager** – Responsible for assembling prompts, applying compression techniques (summarization, truncation, selective inclusion), and caching frequent prompt patterns.
3. **Memory System** – Pluggable short-term memory (in‑memory, SQLite, Redis) storing recent interactions; optional long‑term memory via embeddings or vector store.
4. **Tool Executor** – Registry of callable tools (functions) with schema definitions; executes tools safely and returns results to the prompt manager.
5. **Planner / Reasoning Loop** – Implements ReAct‑style loop: think → act → observe, with configurable max iterations.
6. **Self‑Reflection Module** – Optional step after each reasoning loop where the agent critiques its own output and refines the prompt.
7. **Observability & Telemetry** – Token counters, cost estimator, latency metrics, and structured logging.
8. **Configuration Loader** – Reads YAML/env settings for model, temperature, token limits, memory backend, etc.
9. **Agent Orchestrator** – Public API class that ties all components together, providing `run(task)` and `async_run(task)` methods.

## Data Flow
1. User provides a task string.
2. Prompt Manager builds initial prompt using system message, available tools description, and relevant memories.
3. LLM Interface calls the OpenAI API, returns a completion.
4. Planner parses the completion for thought, action, and action input.
5. If an action is present, Tool Executor runs the tool, returns observation.
6. Observation is fed back into the prompt (via Prompt Manager) and loop continues until a final answer is produced or max iterations reached.
7. Optionally, Self‑Reflection module is invoked to improve the final answer.
8. Final answer is returned to user; token usage and cost are logged.

## Cross‑Cutting Concerns
- **Token Budgeting**: Each component reports token usage; Prompt Manager ensures total prompt stays below a configurable threshold (e.g., 2048 tokens) by applying compression.
- **Extensibility**: New tools are added by registering a Python function with a JSON‑Schema description; new memory backends implement a simple interface (get, add, clear).
- **Safety**: Tool execution is sandboxed (optional) and arguments are validated against the schema.
- **Concurrency**: The core is sync‑first; an async wrapper uses `asyncio.to_thread` for blocking calls, enabling async agents.

## Diagram (textual)
```
+----------------+      +----------------+      +----------------+
|   User Input   | ---> | Prompt Manager | ---> |   LLM API      |
+----------------+      +----------------+      +----------------+
          ^                         |                         |
          |                         v                         v
          |                 +----------------+      +----------------+
          |                 |  Tool Executor | <--- |  Planner/Loop  |
          |                 +----------------+      +----------------+
          |                         ^                         |
          |                         |                         |
          |                 +----------------+      +----------------+
          +---------------- | Self‑Reflection| <---| Observability  |
                           +----------------+      +----------------+
```