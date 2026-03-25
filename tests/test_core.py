"""Tests for the TrendSeer core engine."""

from datetime import datetime, timedelta, timezone

from trendseer.core import (
    AnomalyDetector,
    Signal,
    TimeSeries,
    TopicCluster,
    Trend,
    TrendDetector,
    TrendResults,
    TrendScorer,
)


class TestSignal:
    def test_keywords_extraction(self):
        signal = Signal(text="Python and Rust are trending on GitHub", source="test")
        kws = signal.keywords
        assert "python" in kws
        assert "rust" in kws
        assert "trending" in kws
        assert "github" in kws
        # Stop words should be excluded
        assert "and" not in kws
        assert "are" not in kws
        assert "on" not in kws


class TestAnomalyDetector:
    def test_z_scores_normal(self):
        detector = AnomalyDetector(threshold=2.0)
        values = [10, 10, 10, 10, 10, 10, 10]
        scores = detector.z_scores(values)
        assert all(z == 0.0 for z in scores)

    def test_detect_anomaly(self):
        detector = AnomalyDetector(threshold=2.0)
        # Steady values with a spike at the end
        values = [5, 5, 5, 5, 5, 5, 5, 5, 5, 50]
        anomalies = detector.detect(values)
        # The last value (50) should be flagged
        assert len(anomalies) >= 1
        indices = [idx for idx, _ in anomalies]
        assert 9 in indices

    def test_velocity_increasing(self):
        detector = AnomalyDetector()
        values = [1, 1, 1, 2, 3, 5, 8]
        vel = detector.velocity(values)
        assert vel > 0

    def test_velocity_flat(self):
        detector = AnomalyDetector()
        values = [5, 5, 5, 5, 5, 5, 5]
        vel = detector.velocity(values)
        assert vel == 0.0


class TestTimeSeries:
    def test_add_and_total(self):
        ts = TimeSeries("python", window_days=7)
        now = datetime.now(timezone.utc)
        ts.add(now, weight=3.0)
        ts.add(now, weight=2.0)
        assert ts.total == 5.0

    def test_rolling_average(self):
        ts = TimeSeries("rust", window_days=10)
        now = datetime.now(timezone.utc)
        for i in range(10):
            ts.add(now - timedelta(days=9 - i), weight=float(i + 1))
        avg = ts.rolling_average(window=3)
        assert len(avg) == 8  # 10 - 3 + 1


class TestTrendScorer:
    def test_perfect_score(self):
        scorer = TrendScorer()
        # High z-score, high volume, high velocity
        score = scorer.score(z_score=5.0, total_signals=100.0, velocity=5.0)
        assert score == 1.0

    def test_zero_score(self):
        scorer = TrendScorer()
        score = scorer.score(z_score=0.0, total_signals=0.0, velocity=0.0)
        assert score == 0.0


class TestTrendDetector:
    def test_detect_with_signals(self):
        detector = TrendDetector(zscore_threshold=1.5, window_days=10)
        now = datetime.now(timezone.utc)

        signals = []
        # Create a burst of signals about "langchain" in the last 2 days
        for i in range(20):
            signals.append(
                Signal(
                    text="LangChain framework for LLM applications is amazing",
                    source="hackernews",
                    timestamp=now - timedelta(hours=i),
                    score=5.0,
                )
            )
        # Add some older, sparse signals
        for i in range(3, 10):
            signals.append(
                Signal(
                    text="LangChain released new version",
                    source="github",
                    timestamp=now - timedelta(days=i),
                    score=1.0,
                )
            )

        detector.ingest(signals)
        results = detector.detect()
        assert isinstance(results, TrendResults)

    def test_empty_signals(self):
        detector = TrendDetector()
        results = detector.detect()
        assert len(results) == 0

    def test_results_export(self):
        trend = Trend(
            topic="rust",
            score=0.85,
            velocity=1.2,
            signal_count=42,
            first_seen=datetime(2026, 1, 1, tzinfo=timezone.utc),
            sources=["github", "hackernews"],
            related_keywords=["cargo", "wasm"],
        )
        results = TrendResults([trend])

        json_out = results.to_json()
        assert '"rust"' in json_out
        assert '"score": 0.85' in json_out

        csv_out = results.to_csv()
        assert "topic,score" in csv_out
        assert "rust" in csv_out


class TestTopicCluster:
    def test_cluster_related_keywords(self):
        clusterer = TopicCluster(min_overlap=0.3)
        signals = [
            Signal(text="Python machine learning framework", source="a"),
            Signal(text="Python machine learning tutorial", source="b"),
            Signal(text="Python machine learning course", source="c"),
            Signal(text="Rust systems programming language", source="d"),
        ]
        clusters = clusterer.cluster(signals)
        assert isinstance(clusters, dict)
        # Python and machine learning should appear together
        found_python_ml = False
        for rep, members in clusters.items():
            if "python" in members and "machine" in members:
                found_python_ml = True
        assert found_python_ml
