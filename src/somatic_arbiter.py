"""The Mocked Somatic Arbiter — Speed First.

Instead of calling an LLM 5 times, we call it 1 time with a batched
prompt that forces a strict JSON array with 5 objects.

Each object: {mode, score, one_liner, urgency, risk, novelty}
"""

import json
import asyncio
from typing import Sequence

from openai import AsyncOpenAI

from src.models import Intuition
from src.config import settings
from src.telemetry import emit_event


SYSTEM_PROMPT = """You are the Somatic Arbiter — a fast, messy, System-1-like intuition generator.
Given a user input, emit EXACTLY 5 intuitions representing different cognitive modes.

Respond with a single JSON array. No markdown, no explanation, no preamble.
Each object MUST have these exact keys:
- mode: one of ["Logical", "Empathetic", "Creative", "Cautious", "Opportunistic"]
- score: float 0.0–1.0 (confidence)
- one_liner: string ≤ 120 chars (the intuition itself)
- urgency: float 0.0–1.0 (how time-sensitive)
- risk: float 0.0–1.0 (how risky if wrong)
- novelty: float 0.0–1.0 (how unconventional)

Example:
[
  {"mode":"Logical","score":0.9,"one_liner":"Break the problem into sub-tasks","urgency":0.7,"risk":0.2,"novelty":0.1},
  {"mode":"Empathetic","score":0.8,"one_liner":"Acknowledge the user\'s frustration first","urgency":0.6,"risk":0.3,"novelty":0.2},
  {"mode":"Creative","score":0.6,"one_liner":"Flip the constraint into a feature","urgency":0.4,"risk":0.7,"novelty":0.9},
  {"mode":"Cautious","score":0.7,"one_liner":"Verify assumptions before proceeding","urgency":0.5,"risk":0.1,"novelty":0.1},
  {"mode":"Opportunistic","score":0.5,"one_liner":"Use this as a pivot to upsell","urgency":0.3,"risk":0.8,"novelty":0.6}
]
"""


class SomaticArbiter:
    """Single-call LLM arbiter that generates 5 intuitions in one batch."""

    def __init__(self, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model

    async def generate(
        self,
        user_input: str,
        session_id: str,
        context: str | None = None,
    ) -> Sequence[Intuition]:
        """Generate 5 intuitions via a single batched LLM call.

        Args:
            user_input: The raw user query
            session_id: For telemetry correlation
            context: Optional session context from the Recency Buffer

        Returns:
            Sequence of 5 Intuition objects
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._build_user_message(user_input, context),
            },
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.9,
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or "[]"

        # Parse the JSON array
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "intuitions" in parsed:
                data = parsed["intuitions"]
            elif isinstance(parsed, list):
                data = parsed
            else:
                # Try to find a list inside the dict
                data = next((v for v in parsed.values() if isinstance(v, list)), [])
        except json.JSONDecodeError:
            data = []

        intuitions = [Intuition(**item) for item in data if self._validate_item(item)]

        # Fallback: if parsing fails or returns fewer than 5, pad with safe defaults
        while len(intuitions) < 5:
            intuitions.append(self._default_intuition(len(intuitions)))

        # Telemetry
        emit_event(
            event_type="somatic_arbiter_output",
            session_id=session_id,
            payload={
                "user_input": user_input,
                "context_present": context is not None,
                "intuitions_count": len(intuitions),
                "intuitions": [i.model_dump() for i in intuitions],
            },
        )

        return intuitions[:5]

    def _build_user_message(self, user_input: str, context: str | None) -> str:
        parts = [f"User input: {user_input}"]
        if context:
            parts.append(f"Session context: {context}")
        parts.append("Generate the 5 intuitions now.")
        return "\n".join(parts)

    def _validate_item(self, item: dict) -> bool:
        required = {"mode", "score", "one_liner", "urgency", "risk", "novelty"}
        return required.issubset(item.keys())

    def _default_intuition(self, idx: int) -> Intuition:
        modes = ["Logical", "Empathetic", "Creative", "Cautious", "Opportunistic"]
        return Intuition(
            mode=modes[idx % 5],
            score=0.5,
            one_liner="Default safe intuition — parsing fallback triggered",
            urgency=0.5,
            risk=0.3,
            novelty=0.2,
        )
