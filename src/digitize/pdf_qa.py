"""PDF quality assurance — verify the generated PDF matches the source image."""

from __future__ import annotations

from pathlib import Path

from digitize.client import ClaudeClient
from digitize.parsing import parse_json_response

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
    """Run QA check on a generated PDF. Returns (passed, message)."""
    response = client.analyze(
        pdf_path,
        SYSTEM_PROMPT,
        "This PDF was generated from an engineering drawing image. "
        "Verify it is complete and legible. Return your assessment as JSON.",
    )

    result = parse_json_response(response)
    if result is None:
        return False, f"Could not parse QA response: {response[:200]}"
    passed = result.get("passed", False)
    issues = result.get("issues", [])
    msg = "; ".join(issues) if issues else "OK"
    return passed, msg
