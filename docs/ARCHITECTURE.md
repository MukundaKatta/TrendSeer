# TrendSeer Architecture

## Overview

TrendSeer uses a pipeline architecture to transform raw signals into ranked trend results.

## Pipeline Stages

### 1. Signal Collection
Signals are collected from multiple sources (RSS feeds, GitHub trending, Hacker News). Each signal is a `Signal` dataclass containing text, source, timestamp, and optional metadata.

### 2. Time Series Construction
Keywords are extracted from signals via tokenization. For each keyword, a `TimeSeries` object tracks daily occurrence counts over a configurable window (default: 30 days).

### 3. Anomaly Detection
The `AnomalyDetector` computes z-scores across each keyword's time series. Keywords with recent z-scores exceeding the threshold (default: 2.0) are flagged as potentially trending.

### 4. Trend Scoring
The `TrendScorer` computes a composite score using three weighted factors:
- **Anomaly strength** (50%): Normalized peak z-score
- **Volume** (20%): Total signal count normalized against a baseline
- **Velocity** (30%): Rate of change between the first and second half of the recent window

### 5. Topic Clustering
The `TopicCluster` groups related keywords using co-occurrence analysis. Keywords that frequently appear together in the same signals are merged into a single topic, named after the highest-frequency keyword in the cluster.

### 6. Results
`TrendResults` provides a sorted list of `Trend` objects with export to JSON and CSV formats.

## Key Design Decisions

- **No ML dependencies**: The engine uses pure statistical methods (z-scores, rolling averages) to avoid heavy dependencies and keep the project lightweight.
- **Source-agnostic ingestion**: The `Signal` dataclass is generic enough to represent data from any source. New sources only need to produce `Signal` objects.
- **Configurable thresholds**: All detection parameters are configurable via `TrendSeerConfig` or constructor arguments.

## Module Map

```
src/trendseer/
  __init__.py      Public API exports
  core.py          Signal, TimeSeries, AnomalyDetector, TrendScorer, TopicCluster, TrendDetector
  config.py        TrendSeerConfig with env-var loading
  utils.py         Logging setup, file export, text helpers
```
