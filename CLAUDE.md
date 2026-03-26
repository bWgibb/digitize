# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

`digitize` is a CLI that extracts structured JSON from engineering drawing images using Claude's vision. Pipeline per drawing: convert to PDF, detect type, QA check, extract content, self-review + fix, write output + index.

## Commands

```bash
make dev                                    # pip install -e ".[dev]"
make test                                   # run offline tests

digitize run drawing.png                    # process a drawing (default: --provider api)
digitize run drawing.png --provider cli     # use Claude Code subscription
digitize run *.png                          # batch — skips already-processed files
digitize run drawings.pdf                   # splits multi-page PDFs, processes each page
digitize run drawing.png --force            # reprocess even if output exists
digitize run drawing.png --skip-verify      # skip self-review step
digitize run drawing.png --skip-qa          # skip PDF quality check
digitize run drawing.png --debug            # write .debug.json with raw LLM responses
digitize run drawing.png --dry-run          # preview without writing files
digitize run drawing.png --type dc_schematic --discipline electrical  # force classification

digitize list                               # show drawing index
digitize init                               # create .digitize/config.json
digitize config                             # show current config
```

## Providers

- `--provider api` (default) — Anthropic SDK. Requires `ANTHROPIC_API_KEY`.
- `--provider cli` — Claude Code CLI subprocess. Sends images as base64 via `--input-format stream-json` (same quality as a direct CC session). No API key needed. Set `DIGITIZE_PROVIDER=cli` as default.

Default model: `claude-opus-4-6`. Override with `--model`.

## Architecture

```
cli.py          Typer entry point. Preflight checks, input validation, batch loop with
                graceful failure, progress counter, summary.
client.py       ClaudeClient.analyze() — single method for images and PDFs. Dispatches
                to Anthropic SDK (_call_api) or Claude CLI (_call_cli). Tracks tokens.
parsing.py      parse_json_response() — shared LLM output parser. Handles markdown
                fencing, preamble text, trailing commentary.
detector.py     Drawing type classification via title block transcription.
extractor.py    Structured extraction with discipline-specific prompts.
verify.py       review_extraction() compares JSON vs source, fix_extraction() applies
                corrections. Both use client.analyze() against the original image.
pdf_qa.py       Checks generated PDF for completeness and legibility.
converter.py    ImageMagick wrapper. Image-to-PDF, PDF page splitting, page counting.
index.py        DRAWING-INDEX.md management. Deduplicates by (drawing number, sheet).
models.py       Pydantic schema: DigitizedDrawing, DrawingType, Component, etc.
config.py       Project config from .digitize/config.json. Default abbreviations.
```

### Prompt system

- `prompts/detect.py` — Classification taxonomy. Requires title block transcription before classifying to prevent misclassification.
- `prompts/extract.py` — Assembles system prompt from common instructions + discipline-specific instructions + project context.
- `prompts/disciplines/` — Per-discipline extraction instructions. Each module exports `TYPES: dict[str, str]`.

To add a new drawing type: add to `detect.py` taxonomy, add extraction instructions in `prompts/disciplines/`.

## Dependencies

- `anthropic` — only needed for `--provider api`
- `typer` + `rich` — CLI and terminal output
- `pydantic` — data models
- ImageMagick (`magick` command) — image/PDF conversion
- `claude` CLI — only needed for `--provider cli`
