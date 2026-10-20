"""Per-user cache paths for downloaded Objection Engine data."""

from pathlib import Path

from platformdirs import user_cache_path


def cache_path() -> Path:
    """Return the platform's cache directory for objectionengine2."""
    return user_cache_path("objectionengine2", appauthor=False)


def assets_path() -> Path:
    return cache_path() / "assets"


def models_path() -> Path:
    return cache_path() / "models"
