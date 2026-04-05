"""I/O helpers for canonical tracker assets."""

from __future__ import annotations

from typing import Any

__all__ = ["fetch_tracker_assets", "inspect_fetched_tracker_assets"]


def fetch_tracker_assets(*args: Any, **kwargs: Any):
    from .fetch_tracker_assets import fetch_tracker_assets as _fetch_tracker_assets

    return _fetch_tracker_assets(*args, **kwargs)


def inspect_fetched_tracker_assets(*args: Any, **kwargs: Any):
    from .fetch_tracker_assets import inspect_fetched_tracker_assets as _inspect_fetched_tracker_assets

    return _inspect_fetched_tracker_assets(*args, **kwargs)
