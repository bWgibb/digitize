"""Tests for Pydantic models (no API calls needed)."""

from digitize.models import DigitizedDrawing, DrawingType, Component


def test_drawing_type_defaults():
    dt = DrawingType(discipline="electrical", primary="dc_schematic")
    assert dt.confidence == "high"
    assert dt.secondary is None


def test_digitized_drawing_minimal():
    data = {
        "drawing": {
            "number": "W-001",
            "sheet": "1",
            "revision": "0",
            "title": "Test",
            "source_file": "test.png",
            "digitized_date": "2025-01-01",
        },
        "drawing_type": {
            "discipline": "electrical",
            "primary": "dc_schematic",
        },
    }
    result = DigitizedDrawing.model_validate(data)
    assert result.drawing.number == "W-001"
    assert result.components == []
    assert result.cables_referenced == []


def test_component_with_attributes():
    c = Component(
        tag="52-1",
        type="breaker",
        description="Main breaker",
        circuit="bus_A",
        attributes={"rating": "1200A"},
    )
    assert c.attributes["rating"] == "1200A"
