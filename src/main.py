"""FastAPI application — REST endpoints for the Cognitive Orchestrator."""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from src.models import OrchestratorRequest, OrchestratorResponse, ArticulationChunk
from src.orchestrator import CognitiveOrchestrator
from src.telemetry import logger
from src.auth import limiter, validate_api_key, get_limiter
from src.config import settings
from src.articulation_cortex_stream import ArticulationCortexStream


_orchestrator: CognitiveOrchestrator | None = None
APP_VERSION = "0.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    _orchestrator = CognitiveOrchestrator()
    logger.info("orchestrator_initialized", version=APP_VERSION)
    yield
    if _orchestrator is not None:
        await _orchestrator.shutdown()
    logger.info("orchestrator_shutdown")


app = FastAPI(
    title="Cognitive Orchestrator API",
    description=(
        "Enterprise-grade cognitive backend with bounded recall, insight spikes, "
        "and pluggable LLM providers (OpenAI / Groq)."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "provider": settings.llm_provider,
    }


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
    """Stream the final articulation as SSE after the cognitive pipeline runs.

    Pipeline stages (arbiter → prune → dialectic → insight) complete first;
    then the synthesis is paced through ArticulationCortexStream for true
    chunked delivery with human-like pauses.
    """
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    async def event_generator():
        result = await _orchestrator.process(request)
        synthesis = result.final_output or result.dialectic_summary or ""

        # Pace the already-generated synthesis as SSE chunks
        async def word_tokens():
            for word in synthesis.split():
                yield word + " "

        streamer = ArticulationCortexStream(
            temp_start=settings.articulation_temp_start,
            temp_end=settings.articulation_temp_end,
            word_chunk_size=6,
            human_pause_chunk=3,
            pause_duration=0.15,
        )
        idx = 0
        async for text in streamer.stream(word_tokens()):
            chunk = ArticulationChunk(
                index=idx,
                text=text,
                temperature=round(streamer.logistic_temp(idx), 4),
            )
            yield f"data: {chunk.model_dump_json()}\n\n"
            idx += 1
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
