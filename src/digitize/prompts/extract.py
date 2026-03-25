"""Base extraction prompt builder that assembles discipline-specific prompts."""

from __future__ import annotations

from digitize.config import ProjectConfig
from digitize.models import DrawingType
from digitize.prompts.disciplines import electrical, instrumentation, mechanical, civil

# Registry of discipline modules
_DISCIPLINE_MODULES = {
    "electrical": electrical.TYPES,
    "instrumentation": instrumentation.TYPES,
    "mechanical": mechanical.TYPES,
    "civil": civil.TYPES,
}

SYSTEM_PROMPT = """\
You are an expert engineering drawing digitizer. You will receive an image \
of an engineering drawing. Your job is to extract all visible information \
into a structured JSON format.

## General Rules

- Extract ONLY what is visible on the drawing. Never guess or infer values \
that are not clearly shown.
- Use "TBD" for any value that is present on the drawing but not legible.
- Omit fields that do not apply to this drawing (do not include empty \
placeholders for irrelevant sections).
- Be thorough: extract every component, terminal, cross-reference, and \
cable visible on the drawing.

## Title Block Extraction

Look in the title block (usually bottom-right) and extract:
- Drawing number, sheet number, revision number
- Title / description
- Equipment name and series
- Section number (if applicable)
- Location / project
- Manufacturer / designer
- Customer name and reference number
- Date and drawing status
- Full revision history table if visible

## Component Extraction

For EVERY component visible on the drawing, add an entry to the "components" \
array with:
- tag: the component designation/tag as shown on the drawing
- type: component type (fuse, relay, contact, breaker, switch, motor, \
valve, transmitter, etc.)
- description: brief description of the component's function
- circuit: which functional circuit/group this component belongs to
- attributes: any additional properties (ratings, positions, states, etc.)

## Cross-References

Extract ALL cross-references shown on the drawing:
- Panel/cubicle references (e.g., "1100-A-2", "50D-E-3")
- Sheet cross-references (e.g., "110A-B-3")
- Detail references (e.g., "SEE DET A/S5")
- Drawing references (e.g., "SEE DWG W-082241")

## Terminal Strips and Test Blocks

- Extract terminal strip designations and all terminal numbers visible
- Extract test block designations and positions

## Cable References

- Extract any cable numbers/designations with from/to if shown

## Cross-Reference Tables

- If the drawing contains reference tables (e.g., switch position tables, \
relay contact tables), extract them as structured data under \
"cross_reference_tables".

{type_specific_instructions}

{project_context_instructions}

## Response Format

Respond with ONLY a JSON object (no markdown fencing). Use the following \
top-level structure:

{{
  "drawing": {{
    "number": "", "sheet": "", "revision": "", "title": "",
    "equipment": "", "series": "", "section": "", "location": "",
    "manufacturer": "", "customer": "", "customer_ref": "",
    "date": "", "status": ""
  }},
  "revisions": [
    {{"rev": 0, "date": "YYYY-MM-DD", "description": ""}}
  ],
  "content": {{
    ... type-specific content as described above ...
  }},
  "components": [
    {{"tag": "", "type": "", "description": "", "circuit": "", "attributes": {{}}}}
  ],
  "terminal_strips": {{
    "TB1": {{"description": "", "terminals": []}}
  }},
  "test_blocks": {{}},
  "cross_references": [
    {{"ref": "", "description": ""}}
  ],
  "cross_reference_tables": {{}},
  "cables_referenced": [
    {{"cable": "", "from_location": "", "to_location": "", "function": ""}}
  ],
  "notes": []
}}
"""


def build_extraction_prompt(
    drawing_type: DrawingType,
    config: ProjectConfig | None = None,
) -> tuple[str, str]:
    """Build the system and user prompts for extraction.

    Returns (system_prompt, user_prompt).
    """
    # Get type-specific instructions
    discipline_types = _DISCIPLINE_MODULES.get(drawing_type.discipline, {})
    type_instructions = discipline_types.get(drawing_type.primary, "")

    if not type_instructions:
        type_instructions = (
            f"This is a {drawing_type.discipline} / {drawing_type.primary} drawing. "
            "Extract all visible information into the content section using "
            "descriptive keys that match the drawing's content."
        )

    # Build project context instructions
    project_instructions = ""
    if config and config.context_fields:
        fields_str = ", ".join(config.context_fields)
        project_instructions = (
            f"\n## Project Context\n\n"
            f"This drawing is part of the project: {config.project.name}. "
            f"Include a \"project_context\" object in the output with these "
            f"fields: {fields_str}. "
            f"Only populate fields with values directly visible on the drawing "
            f"or clearly inferable from the title block. Use \"TBD\" otherwise."
        )
        if config.unit_tags:
            project_instructions += (
                f"\nKnown unit tags for this project: {', '.join(config.unit_tags)}."
            )
        if config.equipment_tags:
            tags = [f"{t.tag} ({t.type})" for t in config.equipment_tags]
            project_instructions += (
                f"\nKnown equipment: {', '.join(tags)}."
            )

    system = SYSTEM_PROMPT.format(
        type_specific_instructions=type_instructions,
        project_context_instructions=project_instructions,
    )

    user = (
        f"This drawing has been classified as: {drawing_type.discipline} / "
        f"{drawing_type.primary}.\n\n"
        "Extract all information from this drawing into the structured JSON "
        "format described in your instructions."
    )

    return system, user
