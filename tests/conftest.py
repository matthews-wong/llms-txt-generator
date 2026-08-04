"""Shared pytest fixtures pointing at the bundled example site."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SITE = REPO_ROOT / "examples" / "site"
EXAMPLE_SITEMAP = REPO_ROOT / "examples" / "sitemap.xml"
BASE_URL = "https://nimbusnotes.example"


@pytest.fixture
def example_site() -> Path:
    """Path to the bundled example directory of .md/.html pages."""
    return EXAMPLE_SITE


@pytest.fixture
def example_sitemap() -> Path:
    """Path to the bundled example sitemap.xml."""
    return EXAMPLE_SITEMAP


@pytest.fixture
def base_url() -> str:
    """Base URL used when building links for the example site."""
    return BASE_URL
