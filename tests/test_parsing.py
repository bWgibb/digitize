"""Tests for JSON parsing robustness (no API calls needed)."""

from digitize.parsing import parse_json_response


def test_parse_clean_json():
    result = parse_json_response('{"type": "dc_schematic"}')
    assert result == {"type": "dc_schematic"}


def test_parse_json_with_markdown_fence():
    result = parse_json_response('```json\n{"type": "dc_schematic"}\n```')
    assert result == {"type": "dc_schematic"}


def test_parse_json_with_preamble():
    text = 'I\'ll analyze this drawing.\n{"type": "dc_schematic", "confidence": "high"}'
    result = parse_json_response(text)
    assert result is not None
    assert result["type"] == "dc_schematic"


def test_parse_json_with_preamble_and_trailing():
    text = "Here is my analysis:\n{\"type\": \"one_line\"}\nHope this helps!"
    result = parse_json_response(text)
    assert result is not None
    assert result["type"] == "one_line"


def test_parse_garbage_returns_none():
    assert parse_json_response("no json here") is None
    assert parse_json_response("") is None
