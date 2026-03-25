"""Configuration management for TrendSeer."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrendSeerConfig:
    """Central configuration for the TrendSeer engine."""

    # Anomaly detection
    zscore_threshold: float = 2.0
    rolling_window_size: int = 7
    window_days: int = 30

    # Sources
    rss_feeds: list[str] = field(default_factory=list)
    github_token: str = ""
    hn_api_base: str = "https://hacker-news.firebaseio.com/v0"

    # Export
    export_format: str = "json"
    export_dir: str = "./output"

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> TrendSeerConfig:
        """Load configuration from environment variables."""
        feeds_str = os.getenv("RSS_FEEDS", "")
        feeds = [f.strip() for f in feeds_str.split(",") if f.strip()]

        return cls(
            zscore_threshold=float(os.getenv("ZSCORE_THRESHOLD", "2.0")),
            rolling_window_size=int(os.getenv("ROLLING_WINDOW_SIZE", "7")),
            rss_feeds=feeds,
            github_token=os.getenv("GITHUB_TOKEN", ""),
            hn_api_base=os.getenv("HN_API_BASE", "https://hacker-news.firebaseio.com/v0"),
            export_format=os.getenv("EXPORT_FORMAT", "json"),
            export_dir=os.getenv("EXPORT_DIR", "./output"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def ensure_export_dir(self) -> Path:
        """Create export directory if it doesn't exist and return its path."""
        path = Path(self.export_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
