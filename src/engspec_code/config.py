"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """
    Configuration for agent behavior.
    """

    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.0
    regen_count: int = 5
    max_iterations: int = 5


class SwarmConfig(BaseModel):
    """
    Configuration for the agent swarm.
    """

    parallelism: int = 10
    timeout_seconds: int = 600


class EngspecConfig(BaseModel):
    """
    Top-level engspec configuration.
    """

    agent: AgentConfig = Field(default_factory=AgentConfig)
    swarm: SwarmConfig = Field(default_factory=SwarmConfig)
    engspec_dir: str = ".engspec"
    input_file: str = "input.md"
    processed_file: str = "input_processed.md"


def load_config(path: str | Path | None = None) -> EngspecConfig:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to YAML config file. If None, returns defaults.

    Returns:
        Parsed EngspecConfig.
    """
    if path is None:
        return EngspecConfig()

    path = Path(path)
    if not path.exists():
        return EngspecConfig()

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return EngspecConfig(**data)
