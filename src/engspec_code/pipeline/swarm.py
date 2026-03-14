"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engspec_code.config import EngspecConfig
    from engspec_code.parser.engspec_file import EngspecFile


@dataclass
class SwarmResult:
    """
    Result from running the agent swarm.
    """

    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


async def run_swarm(
    engspec_files: list[EngspecFile],
    source_dir: Path,
    processed_input: Path,
    config: EngspecConfig,
) -> SwarmResult:
    """
    Launch the agent swarm to fill and validate .engspec files.

    Each agent independently processes one .engspec file:
    1. Reads skeleton .engspec + source file + input_processed.md
    2. Fills in all spec sections
    3. Runs regeneration verification loop
    4. Returns validated .engspec

    Args:
        engspec_files: List of skeleton .engspec files to process.
        source_dir: Directory containing source files.
        processed_input: Path to input_processed.md.
        config: Engspec configuration.

    Returns:
        SwarmResult with completion status.

    Raises:
        NotImplementedError: Agent swarm not yet implemented.
    """
    raise NotImplementedError(
        "run_swarm requires agent implementation"
    )
