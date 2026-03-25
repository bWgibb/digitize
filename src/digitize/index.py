"""Drawing index management (markdown table)."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from digitize.models import DigitizedDrawing

INDEX_FILENAME = "DRAWING-INDEX.md"

HEADER = """\
# Digitized Drawing Index

| Drawing | Sheet | Rev | Discipline | Type | Description | PDF | JSON |
|---|---|---|---|---|---|---|---|
"""


def update_index(
    output_dir: Path,
    result: DigitizedDrawing,
    pdf_path: Path,
    json_path: Path,
) -> None:
    """Add or update a row in the drawing index."""
    index_path = output_dir / INDEX_FILENAME
    rows = _read_rows(index_path)

    key = (result.drawing.number, result.drawing.sheet)
    new_row = (
        f"| {result.drawing.number} "
        f"| {result.drawing.sheet} "
        f"| {result.drawing.revision} "
        f"| {result.drawing_type.discipline} "
        f"| {result.drawing_type.primary} "
        f"| {result.drawing.title} "
        f"| {pdf_path.name} "
        f"| {json_path.name} |"
    )

    # Replace existing row or append
    updated = False
    for i, (rkey, _) in enumerate(rows):
        if rkey == key:
            rows[i] = (key, new_row)
            updated = True
            break
    if not updated:
        rows.append((key, new_row))

    _write_index(index_path, rows)


def list_index(output_dir: Path, console: Console) -> None:
    """Print the drawing index to the console."""
    index_path = output_dir / INDEX_FILENAME
    if not index_path.exists():
        console.print("[dim]No drawings digitized yet.[/dim]")
        return

    rows = _read_rows(index_path)
    table = Table(title="Digitized Drawings")
    for col in ["Drawing", "Sheet", "Rev", "Discipline", "Type", "Description"]:
        table.add_column(col)

    for _, row_text in rows:
        cells = [c.strip() for c in row_text.strip("|").split("|")]
        # Take first 6 columns for display (skip PDF/JSON filenames)
        table.add_row(*cells[:6])

    console.print(table)
    console.print(f"\n[dim]{len(rows)} drawing(s)[/dim]")


def _read_rows(index_path: Path) -> list[tuple[tuple[str, str], str]]:
    """Read existing index rows. Returns list of ((number, sheet), row_text)."""
    if not index_path.exists():
        return []

    rows = []
    for line in index_path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip header and separator rows
        if len(cells) < 6 or cells[0] in ("Drawing", "---", ""):
            continue
        if all(c.startswith("-") for c in cells):
            continue
        key = (cells[0], cells[1])
        rows.append((key, line))
    return rows


def _write_index(index_path: Path, rows: list[tuple[tuple[str, str], str]]) -> None:
    """Write the full index file."""
    lines = [HEADER.rstrip()]
    for _, row_text in rows:
        lines.append(row_text)
    lines.append(f"\n\n{len(rows)} drawing(s) digitized.\n")
    index_path.write_text("\n".join(lines) + "\n")
