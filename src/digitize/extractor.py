"""Type-specific drawing extraction using Claude vision."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from digitize.client import ClaudeClient
from digitize.config import ProjectConfig
from digitize.models import DigitizedDrawing, DrawingType
from digitize.prompts.extract import build_extraction_prompt


def extract_drawing(
    client: ClaudeClient,
    image_path: Path,
    drawing_type: DrawingType,
    config: ProjectConfig | None,
    pdf_path: Path,
) -> DigitizedDrawing:
    """Extract structured data from a drawing image.

    Sends the image to Claude with type-specific extraction prompts
    and parses the response into a DigitizedDrawing model.
    """
    system_prompt, user_prompt = build_extraction_prompt(drawing_type, config)

    response = client.analyze_image(
        image_path,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=16384,
    )

    data = _parse_response(response)

    # Inject metadata not from the drawing itself
    drawing_data = data.get("drawing", {})
    drawing_data["source_file"] = image_path.name
    drawing_data["digitized_date"] = date.today().isoformat()
    data["drawing"] = drawing_data
    data["drawing_type"] = drawing_type.model_dump()

    # Build project_context from config if applicable
    if config and config.context_fields:
        raw_context = data.get("project_context") or {}
        context = {"project": config.project.code}
        for field in config.context_fields:
            context[field] = raw_context.get(field, "TBD")
        data["project_context"] = context

    return DigitizedDrawing.model_validate(data)


def _parse_response(response: str) -> dict:
    """Parse Claude's JSON response, handling markdown code fencing."""
    text = response.strip()

    # Strip markdown code fencing if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError(
            f"Could not parse extraction response as JSON: {text[:300]}"
        ) from exc
