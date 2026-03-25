"""PDF quality assurance — verify the generated PDF matches the source image."""

from __future__ import annotations

import json
from pathlib import Path

from digitize.client import ClaudeClient

SYSTEM_PROMPT = """\
You are a QA checker for engineering drawing PDFs. You will receive a PDF \
that was converted from a source image. Verify that the PDF is complete and \
legible.

Check:
1. The full drawing is present, including the complete title block
2. No portion of the border, bottom row, or revision table is cut off
3. Text and line work are legible enough to read circuit details
4. The PDF matches the source content (nothing added or removed)

Respond with a JSON object:
{
  "passed": true/false,
  "issues": ["list of issues found, empty if passed"]
}
"""


def qa_pdf(
    client: ClaudeClient,
    pdf_path: Path,
    source_image: Path,
) -> tuple[bool, str]:
    """Run QA check on a generated PDF by sending it to Claude.

    Returns (passed, message).
    """
    response = client.analyze_pdf(
        pdf_path,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=(
            "This PDF was generated from an engineering drawing image. "
            "Verify it is complete and legible. Return your assessment as JSON."
        ),
    )

    result = _parse_json(response)
    if result is None:
        return False, f"Could not parse QA response: {response[:200]}"
    passed = result.get("passed", False)
    issues = result.get("issues", [])
    msg = "; ".join(issues) if issues else "OK"
    return passed, msg


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
