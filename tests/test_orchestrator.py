"""Integration tests for the Core Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator import CognitiveOrchestrator
from src.models import OrchestratorRequest, Intuition, DialecticOutput, ArticulationChunk


class TestOrchestratorFlow:
    """End-to-end flow tests with mocked LLM calls."""

    @pytest.fixture
    def orchestrator(self, mock_openai_client):
        return CognitiveOrchestrator(client=mock_openai_client)

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_response(self, orchestrator):
        """The orchestrator returns a valid OrchestratorResponse."""
        with patch.object(
            orchestrator.arbiter,
            "generate",
            new_callable=AsyncMock,
            return_value=[
                Intuition(
                    mode="Logical",
                    score=0.9,
                    one_liner="Test",
                    urgency=0.8,
                    risk=0.2,
                    novelty=0.1,
                ),
                Intuition(
                    mode="Cautious",
                    score=0.8,
                    one_liner="Test2",
                    urgency=0.7,
                    risk=0.1,
                    novelty=0.1,
                ),
            ],
        ):
            with patch.object(
                orchestrator.council,
                "debate",
                new_callable=AsyncMock,
                return_value=DialecticOutput(
                    option_a_argument="A",
                    option_b_counter="B",
                    synthesis="Synthesis text here",
                ),
            ):
                with patch.object(
                    orchestrator.buffer, "add", new_callable=AsyncMock
                ), patch.object(
                    orchestrator.buffer, "get", new_callable=AsyncMock, return_value=[]
                ), patch.object(
                    orchestrator.buffer, "close", new_callable=AsyncMock
                ):

                    async def mock_articulate(*args, **kwargs):
                        yield ArticulationChunk(index=0, text="Hello", temperature=1.2)
                        yield ArticulationChunk(index=1, text="world.", temperature=0.8)

                    with patch.object(
                        orchestrator.cortex,
                        "articulate",
                        side_effect=mock_articulate,
                    ):
                        request = OrchestratorRequest(user_input="Hello")
                        response = await orchestrator.process(request)

        assert response.final_output is not None
        assert "Hello" in response.final_output or len(response.final_output) > 0
        assert len(response.top_intuitions) > 0
        assert response.session_id is not None
        assert response.latency_ms >= 0
        assert response.log_id is not None

    @pytest.mark.asyncio
    async def test_arbiter_timeout_fallback(self, orchestrator):
        """When arbiter times out, safe defaults are returned."""
        import asyncio

        async def slow_arbiter(*args, **kwargs):
            await asyncio.sleep(10)
            return []

        with patch.object(
            orchestrator.arbiter, "generate", side_effect=slow_arbiter
        ):
            with patch.object(
                orchestrator.council,
                "debate",
                new_callable=AsyncMock,
                return_value=DialecticOutput(
                    option_a_argument="A",
                    option_b_counter="B",
                    synthesis="S",
                ),
            ):
                with patch.object(
                    orchestrator.buffer, "add", new_callable=AsyncMock
                ), patch.object(
                    orchestrator.buffer, "get", new_callable=AsyncMock, return_value=[]
                ), patch.object(
                    orchestrator.buffer, "close", new_callable=AsyncMock
                ):

                    async def mock_articulate(*args, **kwargs):
                        yield ArticulationChunk(
                            index=0, text="Fallback", temperature=1.0
                        )

                    with patch.object(
                        orchestrator.cortex,
                        "articulate",
                        side_effect=mock_articulate,
                    ):
                        request = OrchestratorRequest(user_input="Timeout test")
                        response = await orchestrator.process(request)

        assert response.final_output is not None
        assert response.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_session_id_persistence(self, orchestrator):
        """Provided session_id is preserved through the pipeline."""
        with patch.object(
            orchestrator.arbiter,
            "generate",
            new_callable=AsyncMock,
            return_value=[
                Intuition(
                    mode="Logical",
                    score=0.9,
                    one_liner="T",
                    urgency=0.5,
                    risk=0.5,
                    novelty=0.5,
                ),
            ],
        ):
            with patch.object(
                orchestrator.council,
                "debate",
                new_callable=AsyncMock,
                return_value=DialecticOutput(
                    option_a_argument="A",
                    option_b_counter="B",
                    synthesis="S",
                ),
            ):
                with patch.object(
                    orchestrator.buffer, "add", new_callable=AsyncMock
                ), patch.object(
                    orchestrator.buffer, "get", new_callable=AsyncMock, return_value=[]
                ), patch.object(
                    orchestrator.buffer, "close", new_callable=AsyncMock
                ):

                    async def mock_articulate(*args, **kwargs):
                        yield ArticulationChunk(index=0, text="X", temperature=1.0)

                    with patch.object(
                        orchestrator.cortex,
                        "articulate",
                        side_effect=mock_articulate,
                    ):
                        request = OrchestratorRequest(
                            user_input="Test",
                            session_id="sess-12345",
                        )
                        response = await orchestrator.process(request)

        assert response.session_id == "sess-12345"
