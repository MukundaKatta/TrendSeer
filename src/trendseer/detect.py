"""Emerging-trend detection.

Given a time-bucketed series of term frequencies, score each term on
how sharply it's accelerating relative to its own recent baseline
*and* to the rest of the corpus. The output powers the "what's rising"
leaderboard on the dashboard.

Two complementary scores:
  * **momentum** — recent rate of change vs. longer-window baseline
    (similar to how Twitter's old trending topics worked).
  * **novelty** — how concentrated the term is in the tail of the
    window, i.e. it barely existed before. Keeps slow-burn topics off
    the leaderboard when they aren't really accelerating.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Sequence


@dataclass(frozen=True)
class TrendScore:
    term: str
    momentum: float      # rolling ratio of tail vs. baseline
    novelty: float       # 0..1 — share of total mentions in the tail
    recent_count: int
    total_count: int
    score: float         # combined rank score


def score_terms(
    series: dict[str, Sequence[int]],
    *,
    tail_buckets: int = 3,
    min_total: int = 5,
    smoothing: float = 1.0,
) -> list[TrendScore]:
    """Rank terms by trending-ness given their per-bucket counts.

    `series[term][t]` is the mention count in bucket t. All series must
    have the same length. Buckets should be chronological (oldest first).
    """
    out: list[TrendScore] = []
    for term, counts in series.items():
        total = sum(counts)
        if total < min_total or len(counts) <= tail_buckets:
            continue
        tail = sum(counts[-tail_buckets:])
        head = sum(counts[:-tail_buckets])
        # Normalise by bucket count so different window shapes compare fairly.
        tail_rate = (tail + smoothing) / (tail_buckets + smoothing)
        head_rate = (head + smoothing) / (len(counts) - tail_buckets + smoothing)
        momentum = tail_rate / head_rate
        novelty = tail / total if total else 0.0
        # Log-dampen runaway momentum so a term that 10x'd doesn't
        # dominate a term that 3x'd from a larger base.
        combined = (log(momentum + 1e-9) + 1.0) * (0.5 + 0.5 * novelty) * log(1 + total)
        out.append(TrendScore(
            term=term,
            momentum=round(momentum, 3),
            novelty=round(novelty, 3),
            recent_count=tail,
            total_count=total,
            score=round(combined, 3),
        ))
    out.sort(key=lambda t: t.score, reverse=True)
    return out


def cooling_off(
    series: dict[str, Sequence[int]],
    *,
    tail_buckets: int = 3,
    min_total: int = 5,
) -> list[TrendScore]:
    """Inverse of ``score_terms`` — surface terms that are losing steam."""
    flipped = {k: list(reversed(v)) for k, v in series.items()}
    rising = score_terms(flipped, tail_buckets=tail_buckets, min_total=min_total)
    return rising
