"""Tests for the abstracted LLM client layer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.llm_client import BaseLLMClient, OpenAIClient, GroqClient


class MockLLMClient(BaseLLMClient):
    async def generate(self, messages, **kwargs):
        return "mock response"

    async def generate_stream(self, messages, **kwargs):
        yield "mock "
        yield "stream"


@pytest.mark.asyncio
async def test_mock_llm_client_generate():
    client = MockLLMClient()
    result = await client.generate([{"role": "user", "content": "hello"}])
    assert result == "mock response"


@pytest.mark.asyncio
async def test_mock_llm_client_stream():
    client = MockLLMClient()
    chunks = []
    async for chunk in client.generate_stream([{"role": "user", "content": "hello"}]):
        chunks.append(chunk)
    assert chunks == ["mock ", "stream"]


def test_openai_client_instantiation():
    client = OpenAIClient(api_key="test-key", model="gpt-4o")
    assert client.model == "gpt-4o"


def test_groq_client_instantiation():
    client = GroqClient(api_key="test-key", model="llama3-70b-8192")
    assert client.model == "llama3-70b-8192"


@pytest.mark.asyncio
async def test_openai_client_generate_success():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello world"

    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = mock_cls.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OpenAIClient(api_key="test")
        result = await client.generate([{"role": "user", "content": "hi"}])
        assert result == "Hello world"


@pytest.mark.asyncio
async def test_openai_client_generate_empty_response():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None

    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = mock_cls.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OpenAIClient(api_key="test")
        result = await client.generate([{"role": "user", "content": "hi"}])
        assert result == ""
