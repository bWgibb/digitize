"""Project config loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    name: str = ""
    code: str = ""
    location: str = ""
    owner: str = ""


class EquipmentTag(BaseModel):
    tag: str
    type: str = ""
    note: str = ""


class ProjectConfig(BaseModel):
    project: ProjectInfo = Field(default_factory=ProjectInfo)
    output_dir: str = "digitized"
    abbreviations: dict[str, str] = Field(default_factory=dict)
    equipment_tags: list[EquipmentTag] = Field(default_factory=list)
    unit_tags: list[str] = Field(default_factory=list)
    drawing_series: dict[str, str] = Field(default_factory=dict)
    context_fields: list[str] = Field(default_factory=list)


# Standard abbreviations used when no config overrides them.
DEFAULT_ABBREVIATIONS: dict[str, str] = {
    "BLK": "block",
    "DIAG": "diagram",
    "CTRL": "control",
    "SCHEM": "schematic",
    "COMM": "communication",
    "GEN": "generator",
    "PWR": "power",
    "PROT": "protection",
    "ELEM": "elementary",
    "BKR": "breaker",
    "MTR": "motor",
    "XFMR": "transformer",
    "DIST": "distribution",
    "PNL": "panel",
    "SCHED": "schedule",
    "SLD": "single-line",
    "SWGR": "switchgear",
    "MCC": "motor control center",
    "VFD": "variable frequency drive",
    "UPS": "uninterruptible power supply",
    "CB": "circuit breaker",
    "OVLD": "overload",
    "DISCN": "disconnect",
    "CONT": "contactor",
    "LTG": "lighting",
    "INST": "instrument",
    "RTD": "resistance temperature detector",
    "TC": "thermocouple",
    "ISO": "isometric",
    "HVAC": "heating ventilation air conditioning",
    "STRUCT": "structural",
    "FDTN": "foundation",
    "SECT": "section",
    "DET": "detail",
    "GRND": "grounding",
    "PID": "piping and instrumentation",
}


def load_config(path: Path | None = None) -> ProjectConfig | None:
    """Load project config from a JSON file.

    Search order:
    1. Explicit path argument
    2. .digitize/config.json in current directory
    3. Return None if not found
    """
    candidates = []
    if path is not None:
        if path.is_file():
            candidates.append(path)
        elif path.is_dir():
            candidates.append(path / "config.json")
        else:
            candidates.append(path)
    candidates.append(Path(".digitize/config.json"))

    for candidate in candidates:
        if candidate.exists():
            data = json.loads(candidate.read_text())
            return ProjectConfig.model_validate(data)
    return None


def get_abbreviations(cfg: ProjectConfig | None) -> dict[str, str]:
    """Return merged abbreviation dict (defaults + project overrides)."""
    merged = dict(DEFAULT_ABBREVIATIONS)
    if cfg and cfg.abbreviations:
        merged.update(cfg.abbreviations)
    return merged
