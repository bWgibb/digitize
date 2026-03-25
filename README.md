# digitize

Extract structured data from engineering drawing images using Claude's vision API.

Supports electrical, instrumentation, mechanical, and civil drawings. Outputs JSON with components, cross-references, terminal strips, cables, and full title block metadata.

## Install

```sh
pip install .
```

Requires [ImageMagick](https://imagemagick.org/) (`magick` command) and an [Anthropic API key](https://console.anthropic.com/):

```sh
export ANTHROPIC_API_KEY=sk-ant-...
```

Or use a Claude Code subscription instead:

```sh
export DIGITIZE_PROVIDER=cli
```

## Usage

```sh
digitize run drawing.png
digitize run drawing.png --output-dir output/
digitize run *.png --skip-qa --dry-run
```

The pipeline converts the image to PDF, classifies the drawing type, runs a QA check, then extracts all visible information into structured JSON.

## Project Config

Optionally create a project config to inject context into extraction prompts:

```sh
digitize init
```

This creates `.digitize/config.json` where you can define project-specific abbreviations, known equipment tags, and drawing series.

## Supported Drawing Types

### Electrical
one_line, ac_schematic, dc_schematic, panel_schedule, wiring_diagram, cable_schedule, control_logic, protection_scheme, plc_io_wiring

### Instrumentation
pid, loop_diagram, instrument_index, hookup_drawing, cause_effect, logic_diagram

### Mechanical
equipment_layout, piping_iso, piping_plan, hvac_diagram, equipment_datasheet

### Civil/Structural
site_plan, foundation_plan, structural_steel, grading_plan, section_detail
