"""The Dialectic Council — Constrained Generation.

Passes top 2 intuitions into a second LLM call with:
- max_tokens=256 (strict working memory)
- stop=["|"] (prevents infinite reasoning spillover)
- Jinja2 template forcing debate format

See PDF §3.3 (Dialectic Council) for derivation.
"""

from jinja2 import Template
from openai import AsyncOpenAI

from src.models import Intuition, DialecticOutput
from src.config import settings
from src.telemetry import emit_event


DEBATE_TEMPLATE = Template("""
You are the Dialectic Council. Two intuitions compete. Debate them.

User Input: {{ user_input }}
{% if context %}
Session Context: {{ context }}
{% endif %}

Option A [{{ option_a.mode }} | score {{ option_a.score }}]:
{{ option_a.one_liner }}

Option B [{{ option_b.mode }} | score {{ option_b.score }}]:
{{ option_b.one_liner }}

Format your response EXACTLY as:
Option A says: <argument> |
Option B counters: <counter> |
Synthesis: <final merged stance> |

Be concise. Each segment ≤ 80 words. End with |
""")


class DialecticCouncil:
    """Constrained debate generator with bounded working memory."""

    def __init__(self, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model

    async def debate(
        self,
        option_a: Intuition,
        option_b: Intuition,
        user_input: str,
        session_id: str,
        context: str | None = None,
    ) -> DialecticOutput:
        """Run a constrained debate between two intuitions.

        The stop sequence "|" prevents the model from reasoning
        beyond its allocated 256-token working memory.
        """
        prompt = DEBATE_TEMPLATE.render(
            option_a=option_a,
            option_b=option_b,
            user_input=user_input,
            context=context,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a concise dialectic engine."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.dialectic_max_tokens,
            temperature=0.7,
            stop=[settings.dialectic_stop_sequence],
        )

        raw = response.choices[0].message.content or ""
        parsed = self._parse_debate(raw)

        emit_event(
            event_type="dialectic_council_output",
            session_id=session_id,
            payload={
                "option_a_mode": option_a.mode,
                "option_b_mode": option_b.mode,
                "raw_output": raw,
                "parsed": parsed.model_dump(),
                "tokens_used": response.usage.total_tokens if response.usage else None,
            },
        )

        return parsed

    def _parse_debate(self, raw: str) -> DialecticOutput:
        """Parse the pipe-delimited debate format.

        Falls back gracefully if the model deviates from format.
        """
        parts = [p.strip() for p in raw.split("|") if p.strip()]

        option_a_arg = ""
        option_b_counter = ""
        synthesis = ""

        for part in parts:
            lower = part.lower()
            if lower.startswith("option a says:"):
                option_a_arg = part.split(":", 1)[1].strip()
            elif lower.startswith("option b counters:"):
                option_b_counter = part.split(":", 1)[1].strip()
            elif lower.startswith("synthesis:"):
                synthesis = part.split(":", 1)[1].strip()

        # Fallback: if parsing failed, treat entire raw as synthesis
        if not synthesis and raw:
            synthesis = raw[:500]

        return DialecticOutput(
            option_a_argument=option_a_arg or "No argument extracted",
            option_b_counter=option_b_counter or "No counter extracted",
            synthesis=synthesis or "No synthesis extracted",
        )
