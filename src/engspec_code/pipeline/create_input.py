"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path


def create_input(
    repo_path: str | Path,
    url: str | None = None,
) -> Path:
    """
    Analyze a repository and generate a draft input.md.

    Reads README, CONTRIBUTING, build files, test directories,
    and code structure to produce a draft input.md for human review.

    Args:
        repo_path: Path to the local repository.
        url: Optional git URL to clone first.

    Returns:
        Path to the generated input.md file.

    Raises:
        NotImplementedError: Claude API integration not yet implemented.
    """
    raise NotImplementedError(
        "create_input requires Claude API integration"
    )
