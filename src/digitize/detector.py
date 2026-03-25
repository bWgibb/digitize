"""Drawing type detection using Claude vision."""

from __future__ import annotations

import json
from pathlib import Path

from digitize.client import ClaudeClient
from digitize.models import DrawingType
from digitize.prompts.detect import SYSTEM_PROMPT, USER_PROMPT


def _parse_json(response: str) -> dict | None:
    """Extract a JSON object from a response that may contain surrounding text."""
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


def detect_drawing_type(
    client: ClaudeClient,
    image_path: Path,
    force_discipline: str | None = None,
    force_type: str | None = None,
) -> DrawingType:
    """Detect the discipline and type of an engineering drawing.

    If force_discipline and/or force_type are provided, they override detection.
    """
    if force_discipline and force_type:
        return DrawingType(
            discipline=force_discipline,
            primary=force_type,
            confidence="forced",
            notes="Type was manually specified.",
        )

    if image_path.suffix.lower() == ".pdf":
        response = client.analyze_pdf(
            image_path,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            max_tokens=1024,
        )
    else:
        response = client.analyze_image(
            image_path,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            max_tokens=1024,
        )

    data = _parse_json(response)
    if data is None:
        return DrawingType(
            discipline="unknown",
            primary="unknown",
            confidence="low",
            notes=f"Could not parse detection response: {response[:200]}",
        )

    return DrawingType(
        discipline=force_discipline or data.get("discipline", "unknown"),
        primary=force_type or data.get("type", "unknown"),
        secondary=data.get("secondary_type"),
        confidence=data.get("confidence", "medium"),
        notes=data.get("reasoning", ""),
    )
