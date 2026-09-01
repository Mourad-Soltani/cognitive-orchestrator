"""FastAPI application — REST endpoints for the Cognitive Orchestrator."""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from src.models import OrchestratorRequest, OrchestratorResponse
from src.orchestrator import CognitiveOrchestrator
from src.telemetry import logger
from src.auth import limiter, validate_api_key, get_limiter
from src.config import settings


_orchestrator: CognitiveOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    _orchestrator = CognitiveOrchestrator()
    logger.info("orchestrator_initialized")
    yield
    logger.info("orchestrator_shutdown")


app = FastAPI(
    title="Cognitive Orchestrator API",
    description=(
        "Enterprise-grade cognitive backend with bounded recall, insight spikes, "
        "and pluggable LLM providers (OpenAI / Groq)."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.2.0", "provider": settings.llm_provider}


@app.post("/orchestrate", response_model=OrchestratorResponse)
@limiter.limit(settings.rate_limit)
async def orchestrate(
    request: OrchestratorRequest,
    request_obj: Request,
    api_key: str = Depends(validate_api_key),
) -> OrchestratorResponse:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    try:
        return await _orchestrator.process(request)
    except Exception as e:
        logger.error("orchestrator_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orchestrate/stream")
@limiter.limit(settings.rate_limit)
async def orchestrate_stream(
    request: OrchestratorRequest,
    request_obj: Request,
    api_key: str = Depends(validate_api_key),
) -> StreamingResponse:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    async def event_generator():
        result = await _orchestrator.process(request)
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
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
