import pytest
from src.prompt_manager import PromptTemplate, PromptCache, CompressionStrategy

def test_prompt_template_build():
    tpl = PromptTemplate(system="You are a helpful assistant", tools="search, calculator")
    messages = tpl.build(user="Hello")
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a helpful assistant"
    assert messages[1]["role"] == "system"
    assert "search" in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Hello"

def test_prompt_cache():
    cache = PromptCache(capacity=2)
    cache.put("key1", [{"role": "user", "content": "Hi"}])
    cache.put("key2", [{"role": "user", "content": "Bye"}])
    assert cache.get("key1") == [{"role": "user", "content": "Hi"}]
    cache.put("key3", [{"role": "user", "content": "New"}])
    assert cache.get("key2") is None

def test_truncation():
    def counter(text):
        return len(text)
    strategy = CompressionStrategy(token_counter=counter, max_tokens=20)
    messages = [
        {"role": "user", "content": "Hello world"},
        {"role": "assistant", "content": "Hi there"},
    ]
    result = strategy.truncate(messages, reserve=0)
    total = sum(counter(m["content"]) for m in result)
    assert total <= 20

def test_summarize_when_under_budget():
    def counter(text):
        return len(text)
    def fake_llm(prompt):
        return "summary"
    strategy = CompressionStrategy(token_counter=counter, max_tokens=100)
    messages = [{"role": "user", "content": "short"}]
    result = strategy.summarize(messages, llm=fake_llm)
    assert result == messages

def test_select_tools():
    tools = [
        {"name": "search_web", "description": "Search the internet for information"},
        {"name": "calculate", "description": "Perform mathematical calculations"},
        {"name": "translate", "description": "Translate text between languages"},
    ]
    strategy = CompressionStrategy(token_counter=len, max_tokens=100)
    selected = strategy.select_tools(tools, "search for python")
    assert selected[0]["name"] == "search_web"
