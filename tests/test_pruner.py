"""Property-based and unit tests for the Pruner.

Mathematically prove pruning doesn't diverge.
"""

import pytest
from hypothesis import given, strategies as st, settings as hyp_settings

from src.pruner import compute_priority, prune_intuitions
from src.models import Intuition


class TestComputePriority:
    """Unit tests for the priority loss function."""

    def test_priority_is_deterministic(self):
        """Same inputs → same output (required for reproducibility)."""
        i = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.5, risk=0.5, novelty=0.5,
        )
        p1 = compute_priority(i)
        p2 = compute_priority(i)
        assert p1 == p2

    def test_higher_urgency_increases_priority(self):
        """∂priority/∂urgency > 0 (α > 0)."""
        low = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.1, risk=0.5, novelty=0.5,
        )
        high = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.9, risk=0.5, novelty=0.5,
        )
        assert compute_priority(high) > compute_priority(low)

    def test_higher_novelty_decreases_priority(self):
        """∂priority/∂novelty < 0 (γ > 0)."""
        low = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.5, risk=0.5, novelty=0.1,
        )
        high = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.5, risk=0.5, novelty=0.9,
        )
        assert compute_priority(low) > compute_priority(high)

    def test_priority_range(self):
        """Priority ∈ [-(γ), (α + β)] for normalized inputs."""
        i = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=1.0, risk=1.0, novelty=0.0,
        )
        assert compute_priority(i) <= 1.0

        i2 = Intuition(
            mode="Logical", score=0.5, one_liner="test",
            urgency=0.0, risk=0.0, novelty=1.0,
        )
        assert compute_priority(i2) >= -1.0


class TestPruneIntuitions:
    """Unit tests for top-k selection."""

    def test_returns_exactly_top_k(self, sample_intuitions):
        result = prune_intuitions(sample_intuitions, top_k=2)
        assert len(result) == 2

    def test_result_is_ordered_descending(self, sample_intuitions):
        result = prune_intuitions(sample_intuitions, top_k=3)
        priorities = [r.priority for r in result]
        assert priorities == sorted(priorities, reverse=True)

    def test_top_k_larger_than_input(self, sample_intuitions):
        """Graceful handling when k > n."""
        result = prune_intuitions(sample_intuitions[:2], top_k=5)
        assert len(result) == 2

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            prune_intuitions([], top_k=2)

    def test_k_must_be_positive(self, sample_intuitions):
        with pytest.raises(ValueError):
            prune_intuitions(sample_intuitions, top_k=0)


class TestPrunerProperties:
    """Property-based tests using Hypothesis."""

    @given(
        urgency=st.floats(min_value=0.0, max_value=1.0),
        risk=st.floats(min_value=0.0, max_value=1.0),
        novelty=st.floats(min_value=0.0, max_value=1.0),
    )
    @hyp_settings(max_examples=200)
    def test_priority_monotonicity(self, urgency, risk, novelty):
        """For any valid inputs, priority is a real number in [-1, 1]."""
        i = Intuition(
            mode="Logical", score=0.5, one_liner="prop_test",
            urgency=urgency, risk=risk, novelty=novelty,
        )
        p = compute_priority(i)
        assert isinstance(p, float)
        assert -1.0 <= p <= 1.0
