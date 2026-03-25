"""Utility functions for TrendSeer."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from trendseer.core import TrendResults

logger = logging.getLogger("trendseer")


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the TrendSeer package."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def export_results(results: TrendResults, path: str, fmt: str = "json") -> Path:
    """Export trend results to a file.

    Args:
        results: The TrendResults to export.
        path: Directory to write the output file.
        fmt: Format - 'json' or 'csv'.

    Returns:
        Path to the written file.
    """
    out_dir = Path(path)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if fmt == "csv":
        filepath = out_dir / f"trends_{timestamp}.csv"
        filepath.write_text(results.to_csv(), encoding="utf-8")
    else:
        filepath = out_dir / f"trends_{timestamp}.json"
        filepath.write_text(results.to_json(), encoding="utf-8")

    logger.info("Exported %d trends to %s", len(results), filepath)
    return filepath


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def truncate(text: str, max_length: int = 120) -> str:
    """Truncate text to a maximum length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
