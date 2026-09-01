"""Abstracted LLM Layer — OpenAI + Groq with tenacity retries."""

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List

import httpx
from openai import AsyncOpenAI
from groq import AsyncGroq
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Non-streaming generation with retries."""
        pass

    @abstractmethod
    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Streaming generation with retries."""
        pass


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 10.0):
        self.client = AsyncOpenAI(api_key=api_key, timeout=httpx.Timeout(timeout))
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GroqClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "llama3-8b-8192", timeout: float = 5.0):
        self.client = AsyncGroq(api_key=api_key, timeout=httpx.Timeout(timeout))
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.3, min=0.3, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.3, min=0.3, max=2),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
