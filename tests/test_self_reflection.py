import pytest
from unittest.mock import MagicMock
from src.self_reflection import SelfReflectionModule

def test_critique_disabled():
    mock_llm = MagicMock()
    module = SelfReflectionModule(llm=mock_llm, enabled=False)
    result = module.critique([{"role": "user", "content": "Hi"}])
    assert result is None
    mock_llm.assert_not_called()

def test_critique_enabled():
    mock_llm = MagicMock(return_value="The agent should have asked for clarification.")
    module = SelfReflectionModule(llm=mock_llm, enabled=True)
    conv = [{"role": "user", "content": "What is the weather?"}, {"role": "assistant", "content": "I don't know."}]
    result = module.critique(conv)
    assert result == "The agent should have asked for clarification."
    mock_llm.assert_called_once()

def test_refine_with_critique():
    mock_llm = MagicMock(return_value="Improved answer with proper details.")
    module = SelfReflectionModule(llm=mock_llm, enabled=True)
    result = module.refine("Bad answer", "Missing context")
    assert result == "Improved answer with proper details."

def test_refine_disabled():
    mock_llm = MagicMock()
    module = SelfReflectionModule(llm=mock_llm, enabled=False)
    result = module.refine("Original", "Critique")
    assert result == "Original"
    mock_llm.assert_not_called()
