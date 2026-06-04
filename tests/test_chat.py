import pytest
from unittest.mock import MagicMock, patch
from src.chat import ChatSession
from src.agent import Agent


@pytest.fixture
def mock_agent():
    config = {"llm": {"api_key": "test-key"}}
    with patch("src.agent.OpenAILLM") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Hello there!"
        mock_llm.count_tokens.return_value = 10
        mock_llm.model = "gpt-3.5-turbo"
        mock_llm_cls.return_value = mock_llm
        agent = Agent(config=config)
        return agent


def test_chat_session_send(mock_agent):
    session = ChatSession(mock_agent)
    response = session.send("Hi")
    assert response == "Hello there!"
    assert len(session.history) == 2


def test_chat_session_history(mock_agent):
    session = ChatSession(mock_agent)
    session.send("First")
    session.send("Second")
    assert len(session.history) == 4
    assert session.history[0]["content"] == "First"
    assert session.history[2]["content"] == "Second"


def test_chat_session_clear(mock_agent):
    session = ChatSession(mock_agent)
    session.send("Hi")
    session.clear()
    assert len(session.history) == 0


def test_chat_session_report(mock_agent):
    session = ChatSession(mock_agent)
    session.send("Hi")
    report = session.report()
    assert report["total_calls"] >= 1
