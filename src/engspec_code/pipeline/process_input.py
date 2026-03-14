"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path


def process_input(
    repo_path: str | Path,
    input_path: str | Path | None = None,
) -> tuple[Path, list[Path]]:
    """
    Process input.md into input_processed.md and skeleton .engspec files.

    Claude deep-analyzes the repo using input.md and produces:
    (a) input_processed.md with workflows, call graphs, test coverage
    (b) Skeleton .engspec files (one per source file)

    Args:
        repo_path: Path to the repository root.
        input_path: Path to input.md. Defaults to repo_path/input.md.

    Returns:
        Tuple of (path to input_processed.md, list of .engspec paths).

    Raises:
        NotImplementedError: Claude API integration not yet implemented.
    """
    raise NotImplementedError(
        "process_input requires Claude API integration"
    )
