"""Shared JSON response parsing for LLM outputs."""

from __future__ import annotations

import json


def parse_json_response(response: str) -> dict | None:
    """Extract a JSON object from an LLM response.

    Handles markdown code fencing, preamble text, and trailing commentary.
    Returns None if no valid JSON object can be extracted.
    """
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None
