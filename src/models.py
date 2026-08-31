"""Pydantic schemas for strict I/O validation."""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone


class Intuition(BaseModel):
    """A single intuition emitted by the Somatic Arbiter."""

    mode: Literal["Logical", "Empathetic", "Creative", "Cautious", "Opportunistic"]
    score: float = Field(..., ge=0.0, le=1.0)
    one_liner: str = Field(..., max_length=200)
    urgency: float = Field(0.5, ge=0.0, le=1.0)
    risk: float = Field(0.5, ge=0.0, le=1.0)
    novelty: float = Field(0.5, ge=0.0, le=1.0)


class PrunedIntuition(BaseModel):
    """An intuition after pruning with its priority score."""

    intuition: Intuition
    priority: float


class DialecticInput(BaseModel):
    """Input to the Dialectic Council."""

    option_a: Intuition
    option_b: Intuition
    user_input: str
    context: Optional[str] = None


class DialecticOutput(BaseModel):
    """Output from the Dialectic Council."""

    option_a_argument: str = Field(..., max_length=500)
    option_b_counter: str = Field(..., max_length=500)
    synthesis: str = Field(..., max_length=500)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Thesis(BaseModel):
    """A compressed thesis stored in the Recency Buffer."""

    content: str = Field(..., max_length=500)
    source_debate: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InsightEvent(BaseModel):
    """An insight spike event."""

    triggered: bool
    noise_vector_sample: list[float]
    first_token_prob: Optional[float] = None
    flagged_token: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArticulationChunk(BaseModel):
    """A single chunk from the Articulation Cortex."""

    index: int
    text: str
    temperature: float
    delay_ms: Optional[float] = None


class OrchestratorRequest(BaseModel):
    """User-facing request schema."""

    user_input: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    context_override: Optional[str] = None


class OrchestratorResponse(BaseModel):
    """User-facing response schema."""

    final_output: str
    top_intuitions: list[PrunedIntuition]
    dialectic_summary: Optional[str] = None
    insight_event: InsightEvent
    session_id: str
    latency_ms: float
    log_id: str
