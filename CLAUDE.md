# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

`digitize` is a CLI tool that extracts structured data from engineering drawing images (electrical, instrumentation, mechanical, civil) using Claude's vision API. It takes a drawing image, converts to PDF, classifies it by discipline/type, runs a QA check, then extracts all visible information into a structured JSON output.

## Commands

```bash
# Development setup
make dev                                    # pip install -e ".[dev]"

# Run tests (no API key needed — uses offline fixtures)
make test

# Run tests against live API and record responses
ANTHROPIC_API_KEY=sk-... make test-record

# Run the CLI
digitize run <image_files> --output-dir digitized/

# Useful flags
digitize run drawing.png --dry-run          # preview extraction without writing files
digitize run drawing.png --skip-qa          # skip PDF quality check step
digitize run drawing.png --type dc_schematic --discipline electrical  # force classification
digitize run drawing.png --model claude-sonnet-4-20250514
digitize run drawing.png --provider cli     # use Claude Code subscription instead of API key

# Other commands
digitize init                               # create .digitize/config.json interactively
digitize list                               # list digitized drawings from the index
digitize config                             # show current project config
```

## Providers

Two ways to authenticate with Claude:

- `--provider api` (default) — uses the Anthropic SDK directly. Requires `ANTHROPIC_API_KEY`. Faster and more reliable for image analysis.
- `--provider cli` — uses the `claude` CLI as a subprocess. Requires Claude Code installed and authenticated. Uses subscription credits. Set `DIGITIZE_PROVIDER=cli` to make it the default.

CLI provider note: detection runs against the PDF (not the raw image) because the CLI's Read tool handles PDFs with better text fidelity than large images.

## Architecture

The pipeline runs per image: convert to PDF -> detect type -> QA -> extract -> write JSON -> update index.

Key modules in `src/digitize/`:

- `cli.py` — Typer CLI entry point (`digitize = "digitize.cli:app"`). Orchestrates the pipeline.
- `client.py` — `ClaudeClient` with `analyze_image()` and `analyze_pdf()`. Dispatches to Anthropic SDK or Claude CLI subprocess based on provider.
- `detector.py` — Classifies discipline + drawing type. Accepts images or PDFs.
- `converter.py` — Image to PDF via ImageMagick (`magick` CLI).
- `pdf_qa.py` — Sends the PDF to Claude to verify completeness and legibility.
- `extractor.py` — Sends the image with discipline-specific prompts, returns `DigitizedDrawing`.
- `index.py` — Maintains `DRAWING-INDEX.md` in the output directory.
- `models.py` — Pydantic models for the JSON output schema.
- `config.py` — Project config from `.digitize/config.json`. Includes default engineering abbreviations.

### Prompt system

`prompts/detect.py` — Classification taxonomy. Requires title block transcription before classifying.
`prompts/extract.py` — Assembles extraction prompts from common instructions + discipline-specific instructions.
`prompts/disciplines/` — Per-discipline extraction instructions. Each module exports `TYPES: dict[str, str]`.

To add a new drawing type: add it to `detect.py`'s taxonomy, then add extraction instructions in `prompts/disciplines/`.

## Testing

```bash
make test           # run all tests offline
make test-record    # record new API cassettes (needs ANTHROPIC_API_KEY)
```

Tests in `tests/` cover models, config, and JSON parsing without API calls. Place sample images in `tests/fixtures/` for integration tests.

## Dependencies

- `anthropic` — Claude API (only needed for `--provider api`)
- `typer` + `rich` — CLI and terminal output
- `pydantic` — Data models
- ImageMagick (`magick`) — image to PDF conversion
- `claude` CLI — only needed for `--provider cli`
