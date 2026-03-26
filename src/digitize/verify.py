"""Review extracted JSON against the source drawing and fix errors."""

from __future__ import annotations

import json
from pathlib import Path

from digitize.client import ClaudeClient
from digitize.models import DigitizedDrawing
from digitize.parsing import parse_json_response

REVIEW_SYSTEM_PROMPT = """\
You are a QA reviewer for engineering drawing digitization. You will receive \
an engineering drawing and a JSON extraction of that drawing. Your job is to \
compare them and identify errors.

Check the JSON against the drawing for:
1. Drawing metadata: number, sheet, revision, title — do they match the title block?
2. Components: are all visible components captured? Are tags and types correct?
3. Terminal strips: are designations and terminal numbers accurate?
4. Cross-references: are all sheet/panel/drawing references captured?
5. Cables: are cable numbers and from/to correct?
6. Content sections: does the structured content match what's on the drawing?
7. Fabricated data: is anything in the JSON NOT actually on the drawing?

Respond with ONLY a JSON object:
{
  "passed": true/false,
  "score": 0-100,
  "errors": [
    {"field": "drawing.title", "expected": "what's on the drawing", "got": "what's in the JSON", "severity": "high/medium/low"}
  ],
  "missing": ["list of things on the drawing but not in the JSON"],
  "fabricated": ["list of things in the JSON but not on the drawing"]
}
"""

FIX_SYSTEM_PROMPT = """\
You are correcting a JSON extraction of an engineering drawing. You will \
receive the original drawing, the current JSON extraction, and a review \
identifying errors.

Apply ONLY the corrections identified in the review. Do not add new data \
that is not mentioned in the review. Do not remove data that the review \
did not flag.

For fields flagged as "fabricated": if the correct value is visible on the \
drawing, replace with the correct value. If not visible, use empty string \
instead of "TBD".

Respond with ONLY the corrected JSON object (no markdown fencing). Keep the \
exact same structure as the input.
"""


def review_extraction(
    client: ClaudeClient,
    source_path: Path,
    result: DigitizedDrawing,
) -> dict:
    """Compare extracted JSON against the source drawing."""
    result_json = json.dumps(result.model_dump(), indent=2, default=str)

    response = client.analyze(
        source_path,
        REVIEW_SYSTEM_PROMPT,
        "Here is the JSON extraction of this drawing:\n\n"
        f"```json\n{result_json}\n```\n\n"
        "Compare this JSON against the drawing. Identify any errors, "
        "missing items, or fabricated data. Return your assessment as JSON.",
    )

    return parse_json_response(response) or {
        "passed": False,
        "score": 0,
        "errors": [],
        "missing": [],
        "fabricated": [],
        "raw_response": response[:500],
    }


def fix_extraction(
    client: ClaudeClient,
    source_path: Path,
    result: DigitizedDrawing,
    review: dict,
) -> DigitizedDrawing:
    """Apply review corrections to the extraction."""
    result_json = json.dumps(result.model_dump(), indent=2, default=str)
    review_json = json.dumps(review, indent=2, default=str)

    response = client.analyze(
        source_path,
        FIX_SYSTEM_PROMPT,
        "Here is the current JSON extraction:\n\n"
        f"```json\n{result_json}\n```\n\n"
        "Here is the review identifying errors:\n\n"
        f"```json\n{review_json}\n```\n\n"
        "Apply the corrections and return the fixed JSON.",
        max_tokens=16384,
    )

    fixed_data = parse_json_response(response)
    if fixed_data is None:
        return result

    # Preserve source metadata that shouldn't change
    fixed_data["drawing"]["source_file"] = result.drawing.source_file
    fixed_data["drawing"]["digitized_date"] = result.drawing.digitized_date
    fixed_data["drawing_type"] = result.drawing_type.model_dump()

    return DigitizedDrawing.model_validate(fixed_data)
