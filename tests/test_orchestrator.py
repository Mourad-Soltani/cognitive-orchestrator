"""Integration tests for the Core Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator import CognitiveOrchestrator
from src.models import OrchestratorRequest, Intuition, DialecticOutput


class TestOrchestratorFlow:
    """End-to-end flow tests with mocked LLM calls."""

    @pytest.fixture
    def orchestrator(self, mock_openai_client):
        return CognitiveOrchestrator(client=mock_openai_client)

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_response(self, orchestrator):
        """The orchestrator returns a valid OrchestratorResponse."""
        # Mock arbiter
        with patch.object(
            orchestrator.arbiter, "generate",
            return_value=[
                Intuition(mode="Logical", score=0.9, one_liner="Test",
                          urgency=0.8, risk=0.2, novelty=0.1),
                Intuition(mode="Cautious", score=0.8, one_liner="Test2",
                          urgency=0.7, risk=0.1, novelty=0.1),
            ],
        ):
            # Mock council
            with patch.object(
                orchestrator.council, "debate",
                return_value=DialecticOutput(
                    option_a_argument="A", option_b_counter="B",
                    synthesis="Synthesis text here",
                ),
            ):
                # Mock buffer
                with patch.object(
                    orchestrator.buffer, "push",
                    return_value=MagicMock(),
                ):
                    # Mock cortex
                    async def mock_articulate(*args, **kwargs):
                        from src.models import ArticulationChunk
                        yield ArticulationChunk(index=0, text="Hello", temperature=1.2)
                        yield ArticulationChunk(index=1, text="world.", temperature=0.8)

                    with patch.object(
                        orchestrator.cortex, "articulate",
                        side_effect=mock_articulate,
                    ):
                        request = OrchestratorRequest(user_input="Hello")
                        response = await orchestrator.process(request)

        assert response.final_output is not None
        assert len(response.top_intuitions) > 0
        assert response.session_id is not None
        assert response.latency_ms >= 0
        assert response.log_id is not None

    @pytest.mark.asyncio
    async def test_arbiter_timeout_fallback(self, orchestrator):
        """When arbiter times out, safe defaults are returned."""
        import asyncio

        async def slow_arbiter(*args, **kwargs):
            await asyncio.sleep(10)  # Will definitely timeout
            return []

        with patch.object(orchestrator.arbiter, "generate", side_effect=slow_arbiter):
            with patch.object(orchestrator.council, "debate", return_value=DialecticOutput(
                option_a_argument="A", option_b_counter="B", synthesis="S",
            )):
                with patch.object(orchestrator.buffer, "push", return_value=MagicMock()):
                    async def mock_articulate(*args, **kwargs):
                        from src.models import ArticulationChunk
                        yield ArticulationChunk(index=0, text="Fallback", temperature=1.0)

                    with patch.object(orchestrator.cortex, "articulate", side_effect=mock_articulate):
                        request = OrchestratorRequest(user_input="Timeout test")
                        response = await orchestrator.process(request)

        assert "clarification" in response.final_output.lower() or response.final_output == "Fallback"

    @pytest.mark.asyncio
    async def test_session_id_persistence(self, orchestrator):
        """Provided session_id is preserved through the pipeline."""
        with patch.object(orchestrator.arbiter, "generate", return_value=[
            Intuition(mode="Logical", score=0.9, one_liner="T",
                      urgency=0.5, risk=0.5, novelty=0.5),
        ]):
            with patch.object(orchestrator.council, "debate", return_value=DialecticOutput(
                option_a_argument="A", option_b_counter="B", synthesis="S",
            )):
                with patch.object(orchestrator.buffer, "push", return_value=MagicMock()):
                    async def mock_articulate(*args, **kwargs):
                        from src.models import ArticulationChunk
                        yield ArticulationChunk(index=0, text="X", temperature=1.0)

                    with patch.object(orchestrator.cortex, "articulate", side_effect=mock_articulate):
                        request = OrchestratorRequest(
                            user_input="Test",
                            session_id="sess-12345",
                        )
                        response = await orchestrator.process(request)

        assert response.session_id == "sess-12345"
