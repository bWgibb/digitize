"""Type-specific drawing extraction using Claude vision."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from digitize.client import ClaudeClient
from digitize.config import ProjectConfig
from digitize.models import DigitizedDrawing, DrawingType
from digitize.parsing import parse_json_response
from digitize.prompts.extract import build_extraction_prompt


def extract_drawing(
    client: ClaudeClient,
    image_path: Path,
    drawing_type: DrawingType,
    config: ProjectConfig | None,
    pdf_path: Path,
) -> DigitizedDrawing:
    """Extract structured data from a drawing image."""
    system_prompt, user_prompt = build_extraction_prompt(drawing_type, config)

    response = client.analyze(image_path, system_prompt, user_prompt, max_tokens=16384)

    data = parse_json_response(response)
    if data is None:
        raise ValueError(
            f"Could not parse extraction response as JSON: {response[:300]}"
        )

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
