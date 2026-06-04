# Ollama Bot

A lightweight AI agent harness for Ollama-hosted LLMs with web search, interactive chat, and a web UI.

## Installation

```bash
pip install -e .
```

## Configuration

Edit `config.json` to set your Ollama host, model, and API key:

```json
{
    "llm": {
        "model": "tinyllama:latest",
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1"
    }
}
```

CLI flags override config file values.

## Usage

### Interactive REPL (default)

```bash
ollama-bot
```

Rich terminal UI with markdown rendering, spinner, and colored panels.

### Single task

```bash
ollama-bot "What is the capital of France?"
```

### Web server

```bash
ollama-bot --serve
```

Opens a dark-themed chat UI at `http://localhost:80`. Use `--port` to change port.

## Features

- **Web search** — every chat message auto-searches DuckDuckGo and injects results as context
- **Rich CLI** — markdown rendering, spinner with elapsed time, styled panels
- **Web UI** — FastAPI server with markdown rendering via marked.js
- **ReAct agent** — tool-use reasoning loop for non-chat task execution
- **Telemetry** — per-session cost/usage summary via `/report` command or API
- **Configurable** — `config.json` for host, model, API key, and runtime flags
