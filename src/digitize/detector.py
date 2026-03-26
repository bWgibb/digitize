"""Drawing type detection using Claude vision."""

from __future__ import annotations

from pathlib import Path

from digitize.client import ClaudeClient
from digitize.models import DrawingType
from digitize.parsing import parse_json_response
from digitize.prompts.detect import SYSTEM_PROMPT, USER_PROMPT


def detect_drawing_type(
    client: ClaudeClient,
    image_path: Path,
    force_discipline: str | None = None,
    force_type: str | None = None,
) -> DrawingType:
    """Detect the discipline and type of an engineering drawing."""
    if force_discipline and force_type:
        return DrawingType(
            discipline=force_discipline,
            primary=force_type,
            confidence="forced",
            notes="Type was manually specified.",
        )

    response = client.analyze(image_path, SYSTEM_PROMPT, USER_PROMPT, max_tokens=1024)

    data = parse_json_response(response)
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
