"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from engspec_code.parser.engspec_file import EngspecFile

# Source file extensions we recognize
SOURCE_EXTENSIONS = {
    ".py",
    ".rs",
    ".go",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
}


@dataclass
class SyncReport:
    """
    Report on the synchronization state between source files
    and their .engspec counterparts.
    """

    orphaned_specs: list[str] = field(default_factory=list)
    uncovered_functions: list[str] = field(default_factory=list)
    stale_specs: list[str] = field(default_factory=list)
    covered_functions: list[str] = field(default_factory=list)


def _compute_file_hash(path: Path) -> str:
    """
    Compute sha256 hash of a file.

    Args:
        path: Path to the file.

    Returns:
        Hash string in format "sha256:<hex>".
    """
    h = hashlib.sha256(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def sync_check(source_dir: str | Path, engspec_dir: str | Path) -> SyncReport:
    """
    Compare source files against .engspec files to detect drift.

    Args:
        source_dir: Directory containing source files.
        engspec_dir: Directory containing .engspec files.

    Returns:
        SyncReport detailing orphans, uncovered, stale, and covered.
    """
    source_dir = Path(source_dir)
    engspec_dir = Path(engspec_dir)

    report = SyncReport()

    # Collect source files
    source_files: dict[str, Path] = {}
    for ext in SOURCE_EXTENSIONS:
        for src_path in source_dir.rglob(f"*{ext}"):
            rel = str(src_path.relative_to(source_dir))
            source_files[rel] = src_path

    # Collect engspec files
    engspec_files: dict[str, EngspecFile] = {}
    for esp_path in engspec_dir.rglob("*.engspec"):
        try:
            ef = EngspecFile.parse(esp_path)
            engspec_files[ef.source_path] = ef
        except Exception:
            continue

    # Check for orphaned specs (engspec with no matching source)
    for spec_source in engspec_files:
        if spec_source not in source_files:
            report.orphaned_specs.append(spec_source)

    # Check source files against engspecs
    for rel_path, src_path in source_files.items():
        if rel_path not in engspec_files:
            report.uncovered_functions.append(rel_path)
        else:
            ef = engspec_files[rel_path]
            current_hash = _compute_file_hash(src_path)
            if ef.source_hash and ef.source_hash != current_hash:
                report.stale_specs.append(rel_path)
            else:
                report.covered_functions.append(rel_path)

    return report
