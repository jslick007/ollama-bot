# Prompt Engineering Guide

## Goals
- Minimize token count while preserving necessary context.
- Improve reliability and quality of LLM outputs.
- Enable consistent behavior across runs.

## Core Techniques

### 1. Tool Description Compression
- Instead of dumping full JSON schemas, provide concise natural‑language descriptions.
- Example: Instead of {"name": "search", "parameters": {...}}, use "search(query: string): returns top 5 web results".
- Only include tools likely needed for the current task (dynamic tool selection based on task keywords).

### 2. Memory Summarization
- Keep recent exchanges verbatim (last 2‑3 turns).
- Summarize older exchanges using the same LLM with a prompt like: "Summarize the following conversation in 2 sentences, preserving key facts and decisions."
- Store summaries in memory; when building the prompt, concatenate summaries with recent verbatim turns.

### 3. Selective Context Inclusion
- Before each LLM call, score each memory snippet by relevance to the current task (simple keyword match or lightweight embedding).
- Include only top‑N most relevant snippets.
- Adjust N based on token budget.

### 4. Prompt Caching
- Recurrent prompt patterns (system + tools description) can be cached and reused.
- Compute a hash of the invariant parts; store the tokenized version to avoid re‑encoding.

### 5. Compression‑Aware Token Budgeting
- Define a maximum prompt token limit (e.g., 1500 tokens).
- Subtract estimated completion tokens (based on max_output) to stay within model's context window.
- If the prompt exceeds the limit, apply compression escalation:
  1. Truncate oldest memory turns.
  2. Summarize memory blocks.
  3. Reduce tool descriptions to names only.
  4. As a last resort, truncate the user task (preserve keywords).

### 6. Few‑Shot Examples (Optional)
- For complex reasoning patterns, include 1‑2 solved examples in the prompt.
- Keep examples short; use placeholders for variable parts.
- Cache few‑shot examples as they are static.

### 7. Structured Output Prompting
- When possible, ask the model to output JSON with a defined schema.
- Use prompting like: "Respond with a JSON object containing keys: thought, action, action_input."
- This reduces post‑processing ambiguity and can be parsed reliably.

### 8. Self‑Reflection Prompt
- After a candidate answer, ask: "Critique the following answer for correctness, completeness, and style. List any issues and suggest improvements."
- Feed the critique back into the next iteration or use it to refine the final answer.

## Prompt Template

```
<|system|>
You are a helpful AI agent with access to the following tools:
{tool_descriptions}

You operate under a strict token budget. Be concise in your thoughts and actions.
<|memory|>
{memory_summary}
<|recent|>
{recent_conversation}
<|user|>
{task}
<|agent_scratchpad|>
{agent_scratchpad}
```

Where:
- `{tool_descriptions}`: compressed tool list.
- `{memory_summary}`: summarized older interactions.
- `{recent_conversation}`: last 2‑3 turns (user + agent).
- `{agent_scratchpad}`: accumulated thoughts, actions, observations from the current reasoning loop.

## Implementation Notes
- The Prompt Manager is responsible for filling the template and applying compression.
- Token counting is done via `tiktoken` (if available) or approximate character‑based estimation.
- All techniques are configurable via YAML (enable/disable, thresholds, etc.).
