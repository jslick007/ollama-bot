import pytest
from unittest.mock import MagicMock, patch
from src.llm import OpenAILLM

@pytest.fixture
def llm():
    return OpenAILLM(api_key="fake-key", model="gpt-3.5-turbo")

def test_count_tokens(llm):
    with patch("tiktoken.encoding_for_model") as mock_encoding_for_model:
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]
        mock_encoding_for_model.return_value = mock_encoding
        
        tokens = llm.count_tokens("Hello world")
        assert tokens == 5
        mock_encoding_for_model.assert_called_once_with("gpt-3.5-turbo")

def test_generate_non_streaming(llm):
    with patch("openai.resources.chat.completions.Completions.create") as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there!"
        mock_create.return_value = mock_response
        
        prompt = [{"role": "user", "content": "Hi"}]
        result = llm.generate(prompt)
        
        assert result == "Hello there!"
        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=prompt,
            stream=False
        )

def test_generate_streaming(llm):
    with patch("openai.resources.chat.completions.Completions.create") as mock_create:
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello"
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = " there!"
        
        mock_create.return_value = [mock_chunk1, mock_chunk2]
        
        prompt = [{"role": "user", "content": "Hi"}]
        result = llm.generate(prompt, stream=True)
        
        generated_text = "".join(list(result))
        assert generated_text == "Hello there!"
        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=prompt,
            stream=True
        )

def test_generate_retry(llm):
    with patch("openai.resources.chat.completions.Completions.create") as mock_create:
        import openai
        mock_request = MagicMock()
        # Fail twice, then succeed
        mock_create.side_effect = [
            openai.APIError("Rate limit exceeded", request=mock_request, body=None),
            openai.APIError("Rate limit exceeded", request=mock_request, body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Success"))])
        ]
        
        prompt = [{"role": "user", "content": "Hi"}]
        # Reduce max_retries for faster test
        llm.max_retries = 2
        
        with patch("time.sleep") as mock_sleep:
            result = llm.generate(prompt)
            assert result == "Success"
            assert mock_create.call_count == 3
            assert mock_sleep.call_count == 2
