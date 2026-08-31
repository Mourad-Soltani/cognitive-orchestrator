"""The Pruner — deterministic loss function for intuition ranking.

priority = (α * urgency) + (β * risk) - (γ * novelty)

See PDF §3.2 (Pruning Layer) for mathematical derivation.
"""

import heapq
from typing import Sequence

from src.models import Intuition, PrunedIntuition
from src.config import settings


def compute_priority(intuition: Intuition) -> float:
    """Apply the exact loss function from the architecture spec.

    priority = (α * urgency) + (β * risk) - (γ * novelty)

    Higher priority = more urgent + more risky - less novel.
    Novelty is penalized because unfamiliar paths are expensive
    in a 150ms window.
    """
    alpha = settings.pruner_alpha
    beta = settings.pruner_beta
    gamma = settings.pruner_gamma

    priority = (alpha * intuition.urgency) + (beta * intuition.risk) - (gamma * intuition.novelty)
    return round(priority, 6)


def prune_intuitions(intuitions: Sequence[Intuition], top_k: int | None = None) -> list[PrunedIntuition]:
    """Rank intuitions by priority and return the top K.

    Uses heapq.nlargest for O(n log k) efficiency — critical
    when operating inside a 150ms asyncio timeout.

    Args:
        intuitions: Sequence of raw intuitions from the Somatic Arbiter
        top_k: Number of intuitions to retain (default from settings)

    Returns:
        Ordered list of PrunedIntuition, highest priority first
    """
    k = top_k if top_k is not None else settings.pruner_top_k
    if k < 1:
        raise ValueError(f"top_k must be >= 1, got {k}")
    if len(intuitions) == 0:
        raise ValueError("Cannot prune empty intuition sequence")

    scored = [
        PrunedIntuition(intuition=it, priority=compute_priority(it))
        for it in intuitions
    ]

    # heapq.nlargest is deterministic and O(n log k)
    top = heapq.nlargest(min(k, len(scored)), scored, key=lambda p: p.priority)
    return top
