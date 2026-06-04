import asyncio
import json
import queue
import re
import threading
import time
from typing import AsyncGenerator, Dict, List

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt

from src.agent import Agent

console = Console()

INTENT_SYSTEM = (
    "You are a search query generator. Output 1-3 short keyword-based search queries "
    "that a search engine like Google or DuckDuckGo would understand. "
    "Do NOT answer the user's question. Do NOT write full sentences. "
    "Output one query per line, nothing else. "
    "If no search is needed, output: NO_SEARCH\n\n"
    "Examples:\n"
    "User: What's the capital of France?\n"
    "Output: France capital\n\n"
    "User: Tell me about the latest iPhone\n"
    "Output: iPhone 16 release date specs\n\n"
    "User: How's the weather in Tokyo?\n"
    "Output: Tokyo weather forecast"
)

CHECK_SYSTEM = (
    "Given the question and search results, determine if you have enough information "
    "to answer comprehensively. Reply only: ENOUGH or a follow-up search query."
)

VERIFY_SYSTEM = (
    "You are a fact-checker. Given the search results and an answer, "
    "list any claims in the answer that are NOT supported by the search results. "
    "Be specific. If ALL claims are supported, output only: VERIFIED"
)

CITATION_LINE = (
    "CRITICAL: Every factual claim MUST be followed by a citation number in brackets "
    "like [1] or [2]. Cite the search result number for each claim. "
    "If you cannot cite a source, do not make the claim."
)


class ChatSession:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.history: List[Dict[str, str]] = []
        self.last_search_query: str = ""
        self.search_history: List[str] = []
        self.processing_time: float = 0.0

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}"
            for t in self.agent.tool_registry.definitions()
        )
        system_lines = [
            "You are a helpful AI assistant. Answer the user's question using the web search results provided below.",
            "If the search results contain relevant information, summarize it in your own words.",
            "If the search results are empty or unhelpful, say so and answer based on your own knowledge.",
            CITATION_LINE,
        ]
        system = "\n".join(system_lines)
        if tools_desc:
            system += f"\n\nAvailable tools:\n{tools_desc}"
        messages = [{"role": "system", "content": system}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def _llm_call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                progress.add_task("Thinking...", total=None)
                return self.agent._llm_call_with_telemetry(messages, **kwargs)
        except Exception:
            return self.agent._llm_call_with_telemetry(messages, **kwargs)

    def _determine_intent(self, user_input: str) -> List[str]:
        messages = [
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": user_input},
        ]
        result = self._llm_call(messages).strip()
        raw_queries = [q.strip().strip("\"'") for q in result.split("\n") if q.strip()]
        raw_queries = [q for q in raw_queries if q.upper() != "NO_SEARCH"]

        queries = []
        for q in raw_queries[:3]:
            if len(q) > 80:
                continue
            lower = q.lower()
            if any(
                p in lower
                for p in [
                    "i apologize",
                    "i'm sorry",
                    "i am sorry",
                    "i do not",
                    "i don't",
                    "cannot",
                    "as an ai",
                    "i cannot",
                    "i don't have",
                ]
            ):
                continue
            queries.append(q)

        if not queries:
            queries = [user_input[:80].strip()]

        for q in queries:
            self.search_history.append(q)
            try:
                console.print(f"  [dim]search:[/] {q}")
            except Exception:
                pass
        return queries

    def _recursive_search(
        self, queries: List[str], user_input: str, max_rounds: int = 2
    ) -> str:
        if not queries:
            return ""
        all_results: List[Dict] = []
        for q in queries:
            try:
                results = self.agent.tool_registry.execute(
                    "search_web", query=q, max_results=5
                )
                self.last_search_query = q
                all_results.append({"query": q, "results": results})
            except Exception:
                self.last_search_query = ""
        if not all_results:
            return ""
        for _ in range(max_rounds):
            context = self._format_context(all_results)
            check_messages = [
                {"role": "system", "content": CHECK_SYSTEM},
                {
                    "role": "user",
                    "content": f"Question: {user_input}\n\n{context}",
                },
            ]
            check = self._llm_call(check_messages).strip().strip("\"'")
            if check.upper() == "ENOUGH":
                break
            query = check
            self.search_history.append(query)
            try:
                console.print(f"  [dim]search:[/] {query}")
            except Exception:
                pass
            try:
                results = self.agent.tool_registry.execute(
                    "search_web", query=query, max_results=5
                )
                self.last_search_query = query
                all_results.append({"query": query, "results": results})
            except Exception:
                pass
        return self._format_context(all_results)

    def _format_context(self, results_list: List[Dict]) -> str:
        if not results_list:
            return ""
        context_lines = ["Web search results:"]
        for i, s in enumerate(results_list, 1):
            context_lines.append(f"[{i}] Query: {s['query']}\n{s['results']}")
        return "\n\n".join(context_lines)

    def _self_consistency(self, messages: List[Dict]) -> str:
        answer1 = self._llm_call(messages, temperature=0.3)
        answer2 = self._llm_call(messages, temperature=0.7)
        c1 = len(re.findall(r"\[\d+\]", answer1))
        c2 = len(re.findall(r"\[\d+\]", answer2))
        if abs(len(answer1) - len(answer2)) > 200:
            return answer1 if len(answer1) > len(answer2) else answer2
        return answer1 if c1 >= c2 else answer2

    def _verify_answer(self, response: str, search_context: str) -> str:
        if not search_context:
            return response
        messages = [
            {"role": "system", "content": VERIFY_SYSTEM},
            {
                "role": "user",
                "content": f"Search results:\n{search_context}\n\nAnswer:\n{response}",
            },
        ]
        result = self._llm_call(messages).strip()
        if result.upper() == "VERIFIED":
            try:
                console.print("  [green]verified[/]")
            except Exception:
                pass
            return response
        try:
            console.print(f"  [yellow]fixing:[/] {result[:120]}")
        except Exception:
            pass
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Fix issues in your answer.",
            },
            {"role": "assistant", "content": response},
            {
                "role": "user",
                "content": (
                    f"The following claims are not supported by the search results:\n{result}\n\n"
                    f"Rewrite the answer removing or correcting these claims. Cite sources properly."
                ),
            },
        ]
        return self._llm_call(messages)

    async def stream_send(self, user_input: str) -> AsyncGenerator[Dict, None]:
        put_queue: queue.Queue = queue.Queue()

        def _run():
            try:
                self.last_search_query = ""
                self.search_history.clear()
                self.processing_time = 0.0
                t0 = time.perf_counter()
                self.history.append({"role": "user", "content": user_input})

                queries = self._determine_intent(user_input)
                for q in queries:
                    put_queue.put(("search", {"query": q}))

                search_context = self._recursive_search(queries, user_input)

                for q in self.search_history:
                    if q not in queries:
                        put_queue.put(("search", {"query": q}))

                messages = self._build_messages(user_input)
                if search_context:
                    messages.insert(1, {"role": "system", "content": search_context})

                response = self._self_consistency(messages)
                response = self._verify_answer(response, search_context)

                self.history.append({"role": "assistant", "content": response})
                self.processing_time = time.perf_counter() - t0

                chunks = re.split(r"(?<=[.!?])\s+", response) or [response]
                acc = ""
                for chunk in chunks:
                    acc += chunk + " "
                    put_queue.put(("token", {"text": acc}))
                    time.sleep(0.015)

                put_queue.put(("done", {"processing_time": self.processing_time}))
            except Exception as exc:
                put_queue.put(("error", {"message": f"Processing failed: {exc}"}))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        loop = asyncio.get_running_loop()
        while True:
            event_type, data = await loop.run_in_executor(None, put_queue.get)
            yield {"type": event_type, **data}
            if event_type in ("done", "error"):
                break

    def send(self, user_input: str) -> str:
        self.last_search_query = ""
        self.search_history.clear()
        self.processing_time = 0.0
        t0 = time.perf_counter()
        self.history.append({"role": "user", "content": user_input})
        queries = self._determine_intent(user_input)
        search_context = self._recursive_search(queries, user_input)
        messages = self._build_messages(user_input)
        if search_context:
            messages.insert(1, {"role": "system", "content": search_context})
        response = self._self_consistency(messages)
        response = self._verify_answer(response, search_context)
        self.history.append({"role": "assistant", "content": response})
        self.processing_time = time.perf_counter() - t0
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
    parser.add_argument(
        "--chat", action="store_true", help="Start interactive chat REPL"
    )
    parser.add_argument("--serve", action="store_true", help="Start web server")
    parser.add_argument(
        "--port", type=int, default=None, help="Web server port (default: 80)"
    )
    args = parser.parse_args()

    config = {}
    if args.api_key:
        config["llm"] = {"api_key": args.api_key}

    agent = Agent(config=config, config_path=args.config)

    if args.serve:
        from src.web_server import run_server

        port = (
            args.port
            if args.port is not None
            else agent.config.get("server", {}).get("port", 80)
        )
        run_server(agent, port=port)

    if args.task:
        result = agent.run(args.task)
        print(result)
        print("\n--- Report ---")
        print(json.dumps(agent.report(), indent=2))
    else:
        repl(agent)


if __name__ == "__main__":
    main()
