"""Tests for config loading (no API calls needed)."""

import json
from pathlib import Path

from digitize.config import load_config, get_abbreviations, DEFAULT_ABBREVIATIONS


def test_load_config_none():
    assert load_config(Path("/nonexistent/path")) is None


def test_load_config_from_file(tmp_path):
    cfg_data = {
        "project": {"name": "Test Project", "code": "TP"},
        "output_dir": "out",
        "abbreviations": {"CUSTOM": "custom term"},
    }
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(cfg_data))

    cfg = load_config(cfg_file)
    assert cfg is not None
    assert cfg.project.name == "Test Project"
    assert cfg.abbreviations["CUSTOM"] == "custom term"


def test_get_abbreviations_merges():
    cfg_data = {
        "project": {"name": "Test"},
        "abbreviations": {"BLK": "override", "NEW": "new term"},
    }
    from digitize.config import ProjectConfig

    cfg = ProjectConfig.model_validate(cfg_data)
    abbrevs = get_abbreviations(cfg)
    assert abbrevs["BLK"] == "override"
    assert abbrevs["NEW"] == "new term"
    assert abbrevs["CTRL"] == DEFAULT_ABBREVIATIONS["CTRL"]
