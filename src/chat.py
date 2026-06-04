import json
from typing import Dict, List

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt

from src.agent import Agent

console = Console()


class ChatSession:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.history: List[Dict[str, str]] = []
        self.last_search_query: str = ""

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}"
            for t in self.agent.tool_registry.definitions()
        )
        system_lines = [
            "You are a helpful AI assistant. Answer the user's question using the web search results provided below.",
            "If the search results contain relevant information, summarize it in your own words.",
            "If the search results are empty or unhelpful, say so and answer based on your own knowledge.",
            "Cite sources by number when possible, like [1] or [2].",
        ]
        system = "\n".join(system_lines)
        if tools_desc:
            system += f"\n\nAvailable tools:\n{tools_desc}"
        messages = [{"role": "system", "content": system}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def _llm_call(self, messages: List[Dict[str, str]]) -> str:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                progress.add_task("Thinking...", total=None)
                return self.agent._llm_call_with_telemetry(messages)
        except UnicodeEncodeError:
            return self.agent._llm_call_with_telemetry(messages)

    def send(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        messages = self._build_messages(user_input)
        search_results = []
        try:
            console.print(f"  [dim]search_web:[/] {user_input}")
        except Exception:
            pass
        try:
            results = self.agent.tool_registry.execute(
                "search_web", query=user_input, max_results=5
            )
            self.last_search_query = user_input
            search_results.append({"query": user_input, "results": results})
        except Exception:
            self.last_search_query = ""
            pass
        if search_results:
            context_lines = ["Web search results:"]
            for s in search_results:
                context_lines.append(f"Query: {s['query']}\n{s['results']}")
            context = "\n\n".join(context_lines)
            messages.insert(1, {"role": "system", "content": context})
        response = self._llm_call(messages)
        self.history.append({"role": "assistant", "content": response})
        return response

    def clear(self):
        self.history.clear()
        self.agent.telemetry.reset()

    def report(self) -> Dict:
        return self.agent.report()


def repl(agent: Agent):
    session = ChatSession(agent)
    tools = agent.tool_registry.list_tools()

    info_lines = [
        f"[bold]Model:[/] {agent.llm.model}",
    ]
    if tools:
        info_lines.append(f"[bold]Tools:[/] {', '.join(tools)}")
    info_lines.append("[bold]Commands:[/] /exit  /clear  /report  /help")

    console.print(
        Panel("\n".join(info_lines), title="Ollama Bot Chat", border_style="blue")
    )

    while True:
        try:
            user_input = Prompt.ask("[bold]You[/]").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd == "/exit":
                break
            elif cmd == "/clear":
                session.clear()
                console.print("[dim]Conversation cleared.[/dim]")
                continue
            elif cmd == "/report":
                r = session.report()
                console.print(r)
                continue
            elif cmd == "/help":
                console.print("[bold]Commands:[/]")
                console.print("  /exit    - Exit the chat")
                console.print("  /clear   - Clear conversation history")
                console.print("  /report  - Show telemetry report")
                console.print("  /help    - Show this help")
                continue
            else:
                console.print(f"[red]Unknown command:[/] {cmd}")
                continue

        response = session.send(user_input)
        console.print(Panel(Markdown(response), title="Bot", border_style="green"))
        print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ollama Bot Agent")
    parser.add_argument("task", nargs="?", help="Task to run")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--api-key", "-k", help="OpenAI API key")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat REPL")
    parser.add_argument("--serve", action="store_true", help="Start web server")
    parser.add_argument("--port", type=int, default=80, help="Web server port (default: 80)")
    args = parser.parse_args()

    config = {}
    if args.api_key:
        config["llm"] = {"api_key": args.api_key}

    agent = Agent(config=config, config_path=args.config)

    if args.serve:
        from src.web_server import run_server
        run_server(agent, port=args.port)

    if args.task:
        result = agent.run(args.task)
        print(result)
        print("\n--- Report ---")
        print(json.dumps(agent.report(), indent=2))
    else:
        repl(agent)


if __name__ == "__main__":
    main()
