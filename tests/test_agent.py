from unittest.mock import MagicMock, patch
from src.agent import Agent
from src.config import load_config


def test_agent_init_with_defaults():
    config = {"llm": {"api_key": "test-key"}}
    with patch("src.agent.OpenAILLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        agent = Agent(config=config)
        assert agent.config["llm"]["model"] == "qwen3.5:2b"
        assert agent.tool_registry is not None
        assert agent.memory is not None


def test_agent_register_tool():
    config = {"llm": {"api_key": "test-key"}}
    with patch("src.agent.OpenAILLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        agent = Agent(config=config)

        @agent.register_tool
        def add(a: int, b: int) -> int:
            return a + b

        assert "add" in agent.tool_registry.list_tools()


def test_agent_run_with_mock_llm():
    config = {"llm": {"api_key": "test-key"}}
    with patch("src.agent.OpenAILLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Final Answer: 42"
        mock_llm.count_tokens.return_value = 10
        mock_llm.model = "gpt-3.5-turbo"
        mock_llm_cls.return_value = mock_llm
        agent = Agent(config=config)
        result = agent.run("What is the answer?")
        assert result == "42"


def test_agent_report():
    config = {"llm": {"api_key": "test-key"}}
    with patch("src.agent.OpenAILLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Final Answer: done"
        mock_llm.count_tokens.return_value = 10
        mock_llm.model = "gpt-3.5-turbo"
        mock_llm_cls.return_value = mock_llm
        agent = Agent(config=config)
        agent.run("test")
        report = agent.report()
        assert report["total_calls"] == 1
        assert report["total_tokens"] == 20


def test_load_config():
    config = load_config(overrides={"llm": {"model": "gpt-4"}})
    # External config file should win for the model setting
    assert config["llm"]["model"] == "qwen3.5:2b"
    assert config["planner"]["max_iterations"] == 10
