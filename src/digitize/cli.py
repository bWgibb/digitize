"""CLI entry point for digitize."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from digitize.config import load_config, ProjectConfig
from digitize.converter import convert_image_to_pdf, get_pdf_page_count, split_pdf_to_images
from digitize.client import ClaudeClient
from digitize.detector import detect_drawing_type
from digitize.extractor import extract_drawing
from digitize.index import update_index, list_index, is_processed
from digitize.models import DigitizedDrawing
from digitize.pdf_qa import qa_pdf
from digitize.verify import review_extraction, fix_extraction

app = typer.Typer(
    name="digitize",
    help="Multi-discipline engineering drawing extraction CLI.",
    no_args_is_help=True,
)
console = Console()

VALID_DISCIPLINES = {"electrical", "instrumentation", "mechanical", "civil"}
VALID_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".pdf"}


def _preflight_checks(provider: str) -> None:
    """Verify external dependencies before starting a run."""
    # ImageMagick
    if not shutil.which("magick"):
        console.print("[red]ImageMagick not found.[/red] Install it: https://imagemagick.org/")
        raise typer.Exit(1)

    # Provider-specific checks
    if provider == "api":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            console.print(
                "[red]ANTHROPIC_API_KEY not set.[/red]\n"
                "Set it or use --provider cli for Claude Code subscription."
            )
            raise typer.Exit(1)
    elif provider == "cli":
        if not shutil.which("claude"):
            console.print(
                "[red]Claude Code CLI not found.[/red]\n"
                "Install it: https://docs.anthropic.com/en/docs/claude-code"
            )
            raise typer.Exit(1)
    else:
        console.print(f"[red]Unknown provider: {provider}[/red] (use 'api' or 'cli')")
        raise typer.Exit(1)


def _validate_inputs(
    paths: list[Path],
    force_discipline: str | None,
    force_type: str | None,
) -> list[Path]:
    """Validate input files and options. Returns list of valid paths."""
    # Validate discipline/type options
    if force_discipline and force_discipline not in VALID_DISCIPLINES:
        console.print(
            f"[red]Unknown discipline: {force_discipline}[/red]\n"
            f"Valid: {', '.join(sorted(VALID_DISCIPLINES))}"
        )
        raise typer.Exit(1)

    # Validate input files
    valid = []
    for path in paths:
        if not path.exists():
            console.print(f"[red]File not found: {path}[/red]")
            continue
        if path.suffix.lower() not in VALID_IMAGE_SUFFIXES:
            console.print(
                f"[yellow]Skipping unsupported file type: {path.name}[/yellow] "
                f"(supported: {', '.join(sorted(VALID_IMAGE_SUFFIXES))})"
            )
            continue
        valid.append(path)

    if not valid:
        console.print("[red]No valid input files.[/red]")
        raise typer.Exit(1)

    return valid


@app.command()
def run(
    paths: Annotated[list[Path], typer.Argument(help="Image or PDF file(s) to digitize")],
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
    skip_verify: Annotated[
        bool, typer.Option("--skip-verify", help="Skip verification step")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Write debug report with raw LLM responses")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", help="Reprocess even if already digitized")
    ] = False,
    model: Annotated[
        str, typer.Option("--model", help="Claude model to use")
    ] = "claude-opus-4-6",
    provider: Annotated[
        str, typer.Option("--provider", help="Provider: 'api' or 'cli'")
    ] = os.environ.get("DIGITIZE_PROVIDER", "api"),
) -> None:
    """Digitize one or more engineering drawing images."""
    # Preflight
    _preflight_checks(provider)
    valid_paths = _validate_inputs(paths, force_discipline, force_type)

    cfg = load_config(config_path)
    out = output_dir or Path(cfg.output_dir if cfg else "digitized")
    out.mkdir(parents=True, exist_ok=True)

    client = ClaudeClient(model=model, provider=provider, debug=debug)

    # Expand multi-page PDFs into individual page images
    source_images = _expand_inputs(valid_paths, out, console)
    total = len(source_images)

    succeeded: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for i, path in enumerate(source_images, 1):
        # Skip if already processed
        if not force and not dry_run and is_processed(out, path.name):
            console.print(f"\n[dim]({i}/{total}) Skipping (already processed): {path.name}[/dim]")
            skipped.append(path.name)
            continue

        console.print(f"\n[bold]({i}/{total}) Processing:[/bold] {path.name}")
        client.debug_log.clear()
        client.total_input_tokens = 0
        client.total_output_tokens = 0

        try:
            result, pdf_path, review = _process_one(
                client, path, out, cfg,
                force_discipline=force_discipline,
                force_type=force_type,
                skip_qa=skip_qa,
                skip_verify=skip_verify,
            )
        except Exception as exc:
            console.print(f"  [red]Failed: {exc}[/red]")
            failed.append((path.name, str(exc)))
            if debug:
                _write_debug_report(client, out, path, None)
            continue

        if dry_run:
            console.print(json.dumps(result.model_dump(), indent=2, default=str))
            if debug:
                _write_debug_report(client, out, path, review)
            succeeded.append(path.name)
            continue

        # Write JSON
        json_path = pdf_path.with_suffix(".json")
        console.print("  [dim]Writing JSON...[/dim]")
        json_path.write_text(json.dumps(result.model_dump(), indent=2, default=str))

        # Update index
        console.print("  [dim]Updating index...[/dim]")
        update_index(out, result, pdf_path, json_path)

        if debug:
            _write_debug_report(client, out, path, review)

        _print_summary(result, pdf_path, json_path, review, client)
        succeeded.append(path.name)

    # Batch summary
    if total > 1:
        console.print(f"\n[bold]Batch complete:[/bold] {len(succeeded)} succeeded, {len(skipped)} skipped, {len(failed)} failed")
        for name, err in failed:
            console.print(f"  [red]FAILED[/red] {name}: {err}")


def _process_one(
    client: ClaudeClient,
    path: Path,
    out: Path,
    cfg: ProjectConfig | None,
    force_discipline: str | None = None,
    force_type: str | None = None,
    skip_qa: bool = False,
    skip_verify: bool = False,
) -> tuple[DigitizedDrawing, Path, dict | None]:
    """Run the full pipeline on a single drawing. Returns (result, pdf_path, review)."""
    # Convert to PDF
    console.print("  [dim]Converting to PDF...[/dim]")
    pdf_path = convert_image_to_pdf(path, out)
    console.print(f"  PDF: {pdf_path.name}")

    # Detect
    console.print("  [dim]Detecting drawing type...[/dim]")
    detection = detect_drawing_type(
        client, path,
        force_discipline=force_discipline,
        force_type=force_type,
    )
    console.print(
        f"  Detected: [cyan]{detection.discipline}/{detection.primary}[/cyan]"
        f" ({detection.confidence})"
    )

    # QA
    if not skip_qa:
        console.print("  [dim]QA check...[/dim]")
        qa_ok, qa_msg = qa_pdf(client, pdf_path, path)
        if qa_ok:
            console.print("  QA: [green]passed[/green]")
        else:
            console.print(f"  QA: [yellow]{qa_msg}[/yellow]")

    # Extract
    console.print("  [dim]Extracting content...[/dim]")
    result = extract_drawing(client, path, detection, cfg, pdf_path)

    # Review and fix
    review = None
    if not skip_verify:
        console.print("  [dim]Reviewing extraction...[/dim]")
        review = review_extraction(client, path, result)
        score = review.get("score", "?")
        passed = review.get("passed", False)
        n_errors = len(review.get("errors", []))
        n_missing = len(review.get("missing", []))
        n_fabricated = len(review.get("fabricated", []))

        if passed:
            console.print(f"  Review: [green]passed[/green] (score: {score})")
        else:
            console.print(
                f"  Review: [yellow]{n_errors} errors, "
                f"{n_missing} missing, "
                f"{n_fabricated} fabricated[/yellow] (score: {score})"
            )
            console.print("  [dim]Fixing extraction...[/dim]")
            result = fix_extraction(client, path, result, review)
            console.print("  [green]Fixed[/green]")

    return result, pdf_path, review


def _expand_inputs(
    paths: list[Path], output_dir: Path, console: Console
) -> list[Path]:
    """Expand input paths, splitting multi-page PDFs into per-page images."""
    images: list[Path] = []
    for path in paths:
        if path.suffix.lower() == ".pdf":
            page_count = get_pdf_page_count(path)
            console.print(f"  [dim]Splitting PDF: {path.name} ({page_count} page{'s' if page_count != 1 else ''})[/dim]")
            pages = split_pdf_to_images(path, output_dir / "_pages")
            images.extend(pages)
        else:
            images.append(path)
    return images


def _print_summary(
    result: DigitizedDrawing,
    pdf_path: Path,
    json_path: Path,
    verification: dict | None = None,
    client: ClaudeClient | None = None,
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
    if verification:
        score = verification.get("score", "?")
        n_errors = len(verification.get("errors", []))
        n_missing = len(verification.get("missing", []))
        n_fabricated = len(verification.get("fabricated", []))
        table.add_row("Verify score", str(score))
        table.add_row("Errors / Missing / Fabricated", f"{n_errors} / {n_missing} / {n_fabricated}")
    if client:
        total = client.total_input_tokens + client.total_output_tokens
        table.add_row(
            "Tokens",
            f"{total:,} ({client.total_input_tokens:,} in / {client.total_output_tokens:,} out)",
        )
    table.add_row("PDF", str(pdf_path))
    table.add_row("JSON", str(json_path))
    console.print(table)


def _write_debug_report(
    client: ClaudeClient,
    output_dir: Path,
    source_path: Path,
    verification: dict | None,
) -> None:
    report_path = output_dir / f"{source_path.stem}.debug.json"
    report = {
        "source": str(source_path),
        "model": client.model,
        "provider": client.provider,
        "steps": client.debug_log,
        "verification": verification,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str))
    console.print(f"  Debug report: {report_path}")


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
