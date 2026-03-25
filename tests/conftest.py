"""Shared test fixtures."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_image() -> Path:
    """Path to the sample drawing image used for testing."""
    path = FIXTURES_DIR / "sample.png"
    if not path.exists():
        pytest.skip("No sample image at tests/fixtures/sample.png")
    return path
