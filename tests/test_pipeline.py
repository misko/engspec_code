"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engspec_code.config import EngspecConfig, load_config
from engspec_code.parser.engspec_file import EngspecFile
from engspec_code.pipeline.create_input import create_input
from engspec_code.pipeline.process_input import process_input

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def test_load_default_config():
    """
    Test loading the default configuration.
    """
    config = load_config()
    assert config.agent.model == "claude-sonnet-4-20250514"
    assert config.agent.regen_count == 5
    assert config.swarm.parallelism == 10
    assert config.engspec_dir == ".engspec"


def test_load_config_from_yaml():
    """
    Test loading configuration from YAML file.
    """
    config_path = CONFIGS_DIR / "default.yaml"
    if config_path.exists():
        config = load_config(config_path)
        assert isinstance(config, EngspecConfig)
        assert config.agent.regen_count == 5


def test_load_config_missing_file():
    """
    Test that missing config file returns defaults.
    """
    config = load_config("/nonexistent/path.yaml")
    assert config == EngspecConfig()


def test_create_input_not_implemented():
    """
    Test that create_input raises NotImplementedError.
    """
    with pytest.raises(NotImplementedError):
        create_input("/tmp")


def test_process_input_not_implemented():
    """
    Test that process_input raises NotImplementedError.
    """
    with pytest.raises(NotImplementedError):
        process_input("/tmp")


def test_fixture_engspec_parses():
    """
    Test that the sample fixture .engspec file parses correctly
    and represents a complete validated file.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")
    assert ef.status == "validated"
    assert len(ef.specs) == 3

    # Verify all specs have filled-in sections
    for name, spec in ef.specs.items():
        assert spec.purpose, f"{name} missing purpose"
        assert spec.preconditions, f"{name} missing preconditions"
        assert spec.postconditions, f"{name} missing postconditions"


def test_fixture_input_md_exists():
    """
    Test that the sample input.md fixture exists and has content.
    """
    input_path = FIXTURES_DIR / "sample_input.md"
    assert input_path.exists()
    content = input_path.read_text(encoding="utf-8")
    assert "# Project: sample" in content
    assert "## Description" in content
    assert "## Running Tests" in content
