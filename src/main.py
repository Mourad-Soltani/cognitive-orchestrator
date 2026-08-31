"""FastAPI application — REST endpoints for the Cognitive Orchestrator.

Instant OpenAPI spec generation at /docs and /redoc.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from src.models import OrchestratorRequest, OrchestratorResponse
from src.orchestrator import CognitiveOrchestrator
from src.telemetry import logger


# Global orchestrator instance (in-memory state)
_orchestrator: CognitiveOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage orchestrator lifecycle."""
    global _orchestrator
    _orchestrator = CognitiveOrchestrator()
    logger.info("orchestrator_initialized")
    yield
    logger.info("orchestrator_shutdown")


app = FastAPI(
    title="Cognitive Orchestrator API",
    description=(
        "Reference Implementation of a bounded-recall, insight-spiking "
        "cognitive architecture. See README.md for mathematical cross-references."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/orchestrate", response_model=OrchestratorResponse)
async def orchestrate(request: OrchestratorRequest) -> OrchestratorResponse:
    """Run the full cognitive pipeline on a user input.

    Returns the final output, top intuitions, dialectic summary,
    insight event, and full telemetry correlation IDs.
    """
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        response = await _orchestrator.process(request)
        return response
    except Exception as e:
        logger.error("orchestrator_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orchestrate/stream")
async def orchestrate_stream(request: OrchestratorRequest) -> StreamingResponse:
    """Stream the Articulation Cortex output chunk by chunk.

    Each chunk includes the per-chunk temperature and any
    injected human-like delays.
    """
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    async def event_generator():
        result = await _orchestrator.process(request)
        # Re-run articulation to get streaming chunks
        # (In production, this would be a single streaming call)
        from src.articulation_cortex import ArticulationCortex
        cortex = ArticulationCortex()
        async for chunk in cortex.articulate(
            synthesis=result.dialectic_summary or "",
            session_id=result.session_id,
        ):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


def main() -> None:
    """CLI entrypoint."""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
