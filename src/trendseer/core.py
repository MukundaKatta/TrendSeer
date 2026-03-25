"""Core trend detection engine with statistical anomaly detection."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class Signal:
    """A single data point collected from a source."""

    text: str
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    url: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def keywords(self) -> list[str]:
        """Extract keywords from signal text using simple tokenization."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "shall", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "and", "but", "or", "nor", "not", "so", "yet",
            "both", "either", "neither", "each", "every", "all", "any", "few",
            "more", "most", "other", "some", "such", "no", "only", "own", "same",
            "than", "too", "very", "just", "about", "above", "also", "this", "that",
            "it", "its", "i", "we", "you", "he", "she", "they", "them", "their",
            "what", "which", "who", "how", "when", "where", "why",
        }
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#._-]{1,}", self.text.lower())
        return [t for t in tokens if t not in stop_words and len(t) > 1]


class TimeSeries:
    """Time-series representation of signal frequency for a keyword."""

    def __init__(self, keyword: str, window_days: int = 30) -> None:
        self.keyword = keyword
        self.window_days = window_days
        self._counts: dict[str, float] = defaultdict(float)

    def add(self, timestamp: datetime, weight: float = 1.0) -> None:
        """Add a data point at the given timestamp."""
        day_key = timestamp.strftime("%Y-%m-%d")
        self._counts[day_key] += weight

    @property
    def values(self) -> list[float]:
        """Return daily counts as an ordered list over the window."""
        if not self._counts:
            return []
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=self.window_days - 1)
        result = []
        for i in range(self.window_days):
            day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            result.append(self._counts.get(day, 0.0))
        return result

    @property
    def total(self) -> float:
        return sum(self._counts.values())

    def rolling_average(self, window: int = 7) -> list[float]:
        """Compute rolling average over the time series."""
        vals = self.values
        if len(vals) < window:
            return vals
        result = []
        for i in range(len(vals) - window + 1):
            chunk = vals[i : i + window]
            result.append(sum(chunk) / len(chunk))
        return result


class AnomalyDetector:
    """Detects anomalies in time-series data using z-score analysis."""

    def __init__(self, threshold: float = 2.0) -> None:
        self.threshold = threshold

    @staticmethod
    def mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def std_dev(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        m = AnomalyDetector.mean(values)
        variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def z_scores(self, values: list[float]) -> list[float]:
        """Compute z-scores for each value in the series."""
        m = self.mean(values)
        sd = self.std_dev(values)
        if sd == 0:
            return [0.0] * len(values)
        return [(v - m) / sd for v in values]

    def detect(self, values: list[float]) -> list[tuple[int, float]]:
        """Return indices and z-scores of anomalous points."""
        scores = self.z_scores(values)
        return [(i, z) for i, z in enumerate(scores) if abs(z) >= self.threshold]

    def is_trending_up(self, values: list[float]) -> bool:
        """Check if the recent tail of the series is anomalously high."""
        if len(values) < 3:
            return False
        scores = self.z_scores(values)
        recent = scores[-3:]
        return any(z >= self.threshold for z in recent)

    def velocity(self, values: list[float]) -> float:
        """Compute trend velocity: rate of change in the recent window."""
        if len(values) < 4:
            return 0.0
        recent = values[-7:] if len(values) >= 7 else values
        first_half = recent[: len(recent) // 2]
        second_half = recent[len(recent) // 2 :]
        avg_first = self.mean(first_half) if first_half else 0.0
        avg_second = self.mean(second_half) if second_half else 0.0
        if avg_first == 0:
            return avg_second
        return (avg_second - avg_first) / avg_first


@dataclass
class Trend:
    """A detected trend with scoring metadata."""

    topic: str
    score: float
    velocity: float
    signal_count: int
    first_seen: datetime
    sources: list[str] = field(default_factory=list)
    related_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "score": round(self.score, 4),
            "velocity": round(self.velocity, 4),
            "signal_count": self.signal_count,
            "first_seen": self.first_seen.isoformat(),
            "sources": self.sources,
            "related_keywords": self.related_keywords,
        }


class TrendResults:
    """Container for detected trends with filtering and export."""

    def __init__(self, trends: list[Trend]) -> None:
        self._trends = sorted(trends, key=lambda t: t.score, reverse=True)

    def top(self, n: int = 10) -> list[Trend]:
        return self._trends[:n]

    def filter_by_source(self, source: str) -> list[Trend]:
        return [t for t in self._trends if source in t.sources]

    def to_json(self) -> str:
        return json.dumps([t.to_dict() for t in self._trends], indent=2)

    def to_csv(self) -> str:
        header = "topic,score,velocity,signal_count,first_seen,sources\n"
        rows = []
        for t in self._trends:
            sources = ";".join(t.sources)
            rows.append(
                f'"{t.topic}",{t.score:.4f},{t.velocity:.4f},'
                f'{t.signal_count},"{t.first_seen.isoformat()}","{sources}"'
            )
        return header + "\n".join(rows)

    def __len__(self) -> int:
        return len(self._trends)

    def __iter__(self):
        return iter(self._trends)


class TrendScorer:
    """Scores keywords based on anomaly strength, volume, and velocity."""

    def __init__(
        self,
        anomaly_weight: float = 0.5,
        volume_weight: float = 0.2,
        velocity_weight: float = 0.3,
    ) -> None:
        self.anomaly_weight = anomaly_weight
        self.volume_weight = volume_weight
        self.velocity_weight = velocity_weight

    def score(
        self, z_score: float, total_signals: float, velocity: float
    ) -> float:
        """Compute a composite trend score."""
        norm_z = min(abs(z_score) / 5.0, 1.0)
        norm_vol = min(total_signals / 100.0, 1.0)
        norm_vel = min(max(velocity, 0.0) / 5.0, 1.0)
        return (
            self.anomaly_weight * norm_z
            + self.volume_weight * norm_vol
            + self.velocity_weight * norm_vel
        )


class TopicCluster:
    """Groups related keywords into topic clusters using co-occurrence."""

    def __init__(self, min_overlap: float = 0.3) -> None:
        self.min_overlap = min_overlap

    def cluster(self, signals: list[Signal]) -> dict[str, list[str]]:
        """Build keyword co-occurrence clusters from signals."""
        cooccur: dict[tuple[str, str], int] = Counter()
        keyword_freq: Counter[str] = Counter()

        for signal in signals:
            kws = list(set(signal.keywords))
            for kw in kws:
                keyword_freq[kw] += 1
            for i, a in enumerate(kws):
                for b in kws[i + 1 :]:
                    pair = tuple(sorted([a, b]))
                    cooccur[pair] += 1

        # Build adjacency from strong co-occurrences
        adjacency: dict[str, set[str]] = defaultdict(set)
        for (a, b), count in cooccur.items():
            min_freq = min(keyword_freq[a], keyword_freq[b])
            if min_freq > 0 and count / min_freq >= self.min_overlap:
                adjacency[a].add(b)
                adjacency[b].add(a)

        # Simple connected-components clustering
        visited: set[str] = set()
        clusters: dict[str, list[str]] = {}

        for kw in sorted(keyword_freq, key=keyword_freq.get, reverse=True):  # type: ignore[arg-type]
            if kw in visited:
                continue
            component: list[str] = []
            stack = [kw]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.append(node)
                stack.extend(adjacency.get(node, set()) - visited)
            if component:
                # Name the cluster after the highest-frequency keyword
                representative = max(component, key=lambda k: keyword_freq[k])
                clusters[representative] = sorted(component)

        return clusters


class TrendDetector:
    """Main entry point: collects signals, detects trends, returns results."""

    def __init__(
        self,
        zscore_threshold: float = 2.0,
        window_days: int = 30,
    ) -> None:
        self.zscore_threshold = zscore_threshold
        self.window_days = window_days
        self._signals: list[Signal] = []
        self._sources: list[dict[str, Any]] = []

    def add_source(self, name: str, **kwargs: Any) -> None:
        """Register a data source for collection."""
        self._sources.append({"name": name, **kwargs})

    def ingest(self, signals: list[Signal]) -> None:
        """Directly ingest a batch of signals."""
        self._signals.extend(signals)

    def detect(self) -> TrendResults:
        """Run the full detection pipeline on ingested signals."""
        if not self._signals:
            return TrendResults([])

        # Step 1: Build time series per keyword
        series_map: dict[str, TimeSeries] = {}
        keyword_sources: dict[str, set[str]] = defaultdict(set)
        keyword_first_seen: dict[str, datetime] = {}

        for signal in self._signals:
            for kw in signal.keywords:
                if kw not in series_map:
                    series_map[kw] = TimeSeries(kw, window_days=self.window_days)
                series_map[kw].add(signal.timestamp, weight=max(signal.score, 1.0))
                keyword_sources[kw].add(signal.source)
                if kw not in keyword_first_seen or signal.timestamp < keyword_first_seen[kw]:
                    keyword_first_seen[kw] = signal.timestamp

        # Step 2: Anomaly detection and scoring
        detector = AnomalyDetector(threshold=self.zscore_threshold)
        scorer = TrendScorer()
        clusterer = TopicCluster()
        clusters = clusterer.cluster(self._signals)

        trends: list[Trend] = []
        seen_keywords: set[str] = set()

        for kw, ts in series_map.items():
            if kw in seen_keywords:
                continue
            values = ts.values
            if not values or ts.total < 2:
                continue
            if not detector.is_trending_up(values):
                continue

            z_scores = detector.z_scores(values)
            max_z = max(z_scores[-3:]) if len(z_scores) >= 3 else max(z_scores)
            vel = detector.velocity(values)
            sc = scorer.score(max_z, ts.total, vel)

            related = clusters.get(kw, [kw])
            for r in related:
                seen_keywords.add(r)

            trends.append(
                Trend(
                    topic=kw,
                    score=sc,
                    velocity=vel,
                    signal_count=int(ts.total),
                    first_seen=keyword_first_seen.get(kw, datetime.now(timezone.utc)),
                    sources=sorted(keyword_sources.get(kw, set())),
                    related_keywords=[r for r in related if r != kw],
                )
            )

        return TrendResults(trends)
