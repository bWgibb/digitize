"""CLI entry point for digitize."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from digitize.config import load_config, ProjectConfig
from digitize.converter import convert_image_to_pdf
from digitize.client import ClaudeClient
from digitize.detector import detect_drawing_type
from digitize.extractor import extract_drawing
from digitize.index import update_index, list_index
from digitize.models import DigitizedDrawing
from digitize.pdf_qa import qa_pdf

app = typer.Typer(
    name="digitize",
    help="Multi-discipline engineering drawing extraction CLI.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    paths: Annotated[list[Path], typer.Argument(help="Image file(s) to digitize")],
    output_dir: Annotated[
        Optional[Path], typer.Option("--output-dir", "-o", help="Output directory")
    ] = None,
    config_path: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to project config"),
    ] = None,
    skip_qa: Annotated[
        bool, typer.Option("--skip-qa", help="Skip PDF quality check")
    ] = False,
    force_type: Annotated[
        Optional[str], typer.Option("--type", help="Force drawing type")
    ] = None,
    force_discipline: Annotated[
        Optional[str], typer.Option("--discipline", help="Force discipline")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show extraction without writing")
    ] = False,
    model: Annotated[
        str, typer.Option("--model", help="Claude model to use")
    ] = "claude-sonnet-4-20250514",
    provider: Annotated[
        str, typer.Option("--provider", help="Provider: 'api' (Anthropic SDK) or 'cli' (Claude Code subscription)")
    ] = os.environ.get("DIGITIZE_PROVIDER", "api"),
) -> None:
    """Digitize one or more engineering drawing images."""
    cfg = load_config(config_path)
    out = output_dir or Path(cfg.output_dir if cfg else "digitized")
    out.mkdir(parents=True, exist_ok=True)

    client = ClaudeClient(model=model, provider=provider)

    for path in paths:
        if not path.exists():
            console.print(f"[red]File not found: {path}[/red]")
            continue

        console.print(f"\n[bold]Processing:[/bold] {path.name}")

        # Step 1: Convert to PDF
        console.print("  [dim]Step 1: Converting to PDF...[/dim]")
        pdf_path = convert_image_to_pdf(path, out)
        console.print(f"  PDF: {pdf_path.name}")

        # Step 2: Detect discipline and type
        # CLI provider uses the PDF (better text rendering); API uses the image
        console.print("  [dim]Step 2: Detecting drawing type...[/dim]")
        detect_path = pdf_path if provider == "cli" else path
        detection = detect_drawing_type(
            client,
            detect_path,
            force_discipline=force_discipline,
            force_type=force_type,
        )
        console.print(
            f"  Detected: [cyan]{detection.discipline}/{detection.primary}[/cyan]"
            f" ({detection.confidence})"
        )

        # Step 3: QA the PDF
        if not skip_qa:
            console.print("  [dim]Step 3: QA check...[/dim]")
            qa_ok, qa_msg = qa_pdf(client, pdf_path, path)
            if qa_ok:
                console.print("  QA: [green]passed[/green]")
            else:
                console.print(f"  QA: [yellow]{qa_msg}[/yellow]")

        # Step 4: Extract content
        console.print("  [dim]Step 4: Extracting content...[/dim]")
        result: DigitizedDrawing = extract_drawing(
            client, path, detection, cfg, pdf_path
        )

        if dry_run:
            console.print(
                json.dumps(result.model_dump(), indent=2, default=str)
            )
            continue

        # Step 5: Write JSON
        json_path = pdf_path.with_suffix(".json")
        console.print(f"  [dim]Step 5: Writing JSON...[/dim]")
        json_path.write_text(
            json.dumps(result.model_dump(), indent=2, default=str)
        )

        # Step 6: Update index
        console.print("  [dim]Step 6: Updating index...[/dim]")
        update_index(out, result, pdf_path, json_path)

        # Step 7: Summary
        _print_summary(result, pdf_path, json_path)


def _print_summary(
    result: DigitizedDrawing, pdf_path: Path, json_path: Path
) -> None:
    table = Table(title="Digitization Summary", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Drawing", result.drawing.number)
    table.add_row("Title", result.drawing.title)
    table.add_row("Sheet / Rev", f"{result.drawing.sheet} / {result.drawing.revision}")
    table.add_row(
        "Type",
        f"{result.drawing_type.discipline}/{result.drawing_type.primary}",
    )
    table.add_row("Components", str(len(result.components)))
    table.add_row("Content sections", str(len(result.content)))
    table.add_row("Cross-references", str(len(result.cross_references)))
    table.add_row("Cables", str(len(result.cables_referenced)))
    tbd_count = _count_tbd(result.model_dump())
    table.add_row("TBD values", str(tbd_count))
    table.add_row("PDF", str(pdf_path))
    table.add_row("JSON", str(json_path))
    console.print(table)


def _count_tbd(obj: object) -> int:
    if isinstance(obj, str):
        return 1 if obj.upper() == "TBD" else 0
    if isinstance(obj, dict):
        return sum(_count_tbd(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(_count_tbd(v) for v in obj)
    return 0


@app.command()
def init(
    path: Annotated[
        Path, typer.Option("--path", "-p", help="Config directory")
    ] = Path(".digitize"),
) -> None:
    """Initialize a project config interactively."""
    path.mkdir(parents=True, exist_ok=True)
    config_file = path / "config.json"
    if config_file.exists():
        console.print(f"[yellow]Config already exists: {config_file}[/yellow]")
        raise typer.Exit()

    name = typer.prompt("Project name")
    code = typer.prompt("Project code (short identifier)", default="")
    location = typer.prompt("Project location", default="")
    output_dir = typer.prompt("Output directory", default="digitized")

    cfg = {
        "project": {"name": name, "code": code, "location": location},
        "output_dir": output_dir,
        "abbreviations": {},
        "equipment_tags": [],
        "unit_tags": [],
        "drawing_series": {},
        "context_fields": [],
    }
    config_file.write_text(json.dumps(cfg, indent=2))
    console.print(f"[green]Config created: {config_file}[/green]")


@app.command(name="list")
def list_drawings(
    output_dir: Annotated[
        Optional[Path], typer.Option("--output-dir", "-o")
    ] = None,
    config_path: Annotated[
        Optional[Path], typer.Option("--config", "-c")
    ] = None,
) -> None:
    """List digitized drawings from the index."""
    cfg = load_config(config_path)
    out = output_dir or Path(cfg.output_dir if cfg else "digitized")
    list_index(out, console)


@app.command()
def config(
    config_path: Annotated[
        Optional[Path], typer.Option("--config", "-c")
    ] = None,
) -> None:
    """Show current project config."""
    cfg = load_config(config_path)
    if cfg is None:
        console.print("[dim]No project config found.[/dim]")
        return
    console.print(json.dumps(cfg.model_dump(), indent=2))
