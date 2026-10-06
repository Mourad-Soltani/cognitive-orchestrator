"""API-level tests for health, auth, and the orchestrate endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.models import (
    OrchestratorResponse,
    InsightEvent,
    PrunedIntuition,
    Intuition,
)


def _response() -> OrchestratorResponse:
    return OrchestratorResponse(
        final_output="Ship with a flag.",
        top_intuitions=[
            PrunedIntuition(
                intuition=Intuition(
                    mode="Logical",
                    score=0.9,
                    one_liner="Ship with a flag",
                    urgency=0.7,
                    risk=0.2,
                    novelty=0.1,
                ),
                priority=0.4,
            )
        ],
        dialectic_summary="Ship with a flag.",
        insight_event=InsightEvent(triggered=False, noise_vector_sample=[0.0]),
        session_id="sess-api",
        latency_ms=12.0,
        log_id="log-api",
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEYS", "")
    # Re-import after env so VALID_KEYS stays empty (open auth) for these tests.
    import importlib
    import src.auth as auth
    import src.main as main

    auth.VALID_KEYS = set()
    importlib.reload(auth)
    # Keep the already-constructed app; patch validator to open mode.
    main.validate_api_key = auth.validate_api_key
    with TestClient(main.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.3.0"


def test_orchestrate_returns_pipeline_result(client):
    import src.main as main

    with patch.object(
        main._orchestrator,
        "process",
        new_callable=AsyncMock,
        return_value=_response(),
    ):
        response = client.post(
            "/orchestrate",
            json={"user_input": "Should I pivot?"},
            headers={"X-API-Key": "dev-key"},
        )
    assert response.status_code == 200
    assert response.json()["final_output"] == "Ship with a flag."
    assert response.json()["session_id"] == "sess-api"


def test_stream_emits_sse(client):
    import src.main as main

    with patch.object(
        main._orchestrator,
        "process",
        new_callable=AsyncMock,
        return_value=_response(),
    ):
        response = client.post(
            "/orchestrate/stream",
            json={"user_input": "Should I pivot?"},
            headers={"X-API-Key": "dev-key"},
        )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "Ship" in response.text
    assert "[DONE]" in response.text
