"""Tests for JSON parsing robustness (no API calls needed)."""

from digitize.detector import _parse_json


def test_parse_clean_json():
    result = _parse_json('{"type": "dc_schematic"}')
    assert result == {"type": "dc_schematic"}


def test_parse_json_with_markdown_fence():
    result = _parse_json('```json\n{"type": "dc_schematic"}\n```')
    assert result == {"type": "dc_schematic"}


def test_parse_json_with_preamble():
    text = 'I\'ll analyze this drawing.\n{"type": "dc_schematic", "confidence": "high"}'
    result = _parse_json(text)
    assert result is not None
    assert result["type"] == "dc_schematic"


def test_parse_json_with_preamble_and_trailing():
    text = "Here is my analysis:\n{\"type\": \"one_line\"}\nHope this helps!"
    result = _parse_json(text)
    assert result is not None
    assert result["type"] == "one_line"


def test_parse_garbage_returns_none():
    assert _parse_json("no json here") is None
    assert _parse_json("") is None
