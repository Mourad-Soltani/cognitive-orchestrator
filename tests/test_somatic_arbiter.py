"""Unit tests for somatic arbiter parsing and fallbacks."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.somatic_arbiter import SomaticArbiter


def _payload(items):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps(items)
    return response


@pytest.fixture
def arbiter(mock_openai_client):
    return SomaticArbiter(client=mock_openai_client)


def test_validate_item_requires_all_keys(arbiter):
    assert arbiter._validate_item(
        {
            "mode": "Logical",
            "score": 0.5,
            "one_liner": "x",
            "urgency": 0.1,
            "risk": 0.1,
            "novelty": 0.1,
        }
    )
    assert not arbiter._validate_item({"mode": "Logical"})


def test_build_user_message_includes_context(arbiter):
    msg = arbiter._build_user_message("pivot?", "prior: stay")
    assert "pivot?" in msg
    assert "prior: stay" in msg


def test_default_intuition_cycles_modes(arbiter):
    modes = [arbiter._default_intuition(i).mode for i in range(5)]
    assert modes == ["Logical", "Empathetic", "Creative", "Cautious", "Opportunistic"]


@pytest.mark.asyncio
async def test_generate_pads_to_five_on_partial_json(arbiter):
    arbiter.client.chat.completions.create = AsyncMock(
        return_value=_payload(
            {
                "intuitions": [
                    {
                        "mode": "Logical",
                        "score": 0.9,
                        "one_liner": "Split the work",
                        "urgency": 0.7,
                        "risk": 0.2,
                        "novelty": 0.1,
                    }
                ]
            }
        )
    )
    result = await arbiter.generate("Should I pivot?", "sess-1")
    assert len(result) == 5
    assert result[0].mode == "Logical"
    assert result[0].one_liner == "Split the work"


@pytest.mark.asyncio
async def test_generate_handles_invalid_json(arbiter):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "not-json"
    arbiter.client.chat.completions.create = AsyncMock(return_value=response)
    result = await arbiter.generate("hello", "sess-2")
    assert len(result) == 5
    assert all(i.one_liner.startswith("Default safe intuition") for i in result)
