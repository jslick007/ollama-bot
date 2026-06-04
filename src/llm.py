import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union
import openai
import tiktoken

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class LLMInterface(ABC):
    @abstractmethod
    def generate(self, prompt: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        pass

class OpenAILLM(LLMInterface):
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-3.5-turbo", max_retries: int = 3):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = max_retries
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("httpcore").setLevel(logging.ERROR)
        logging.getLogger("openai").setLevel(logging.ERROR)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        model_name = model or self.model
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            logger.debug(f"Unknown model '{model_name}', falling back to cl100k_base encoding")
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                return 0
        return len(encoding.encode(text))

    def generate(self, prompt: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=prompt,
                    stream=stream,
                    **kwargs
                )
                if stream:
                    return self._handle_stream(response)
                else:
                    return response.choices[0].message.content
            except openai.APIError as e:
                retries += 1
                if retries > self.max_retries:
                    raise e
                wait_time = 2 ** retries
                logger.debug(f"API error: {e}. Retrying in {wait_time}s... ({retries}/{self.max_retries})")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise e

    def _handle_stream(self, response) -> Generator[str, None, None]:
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
