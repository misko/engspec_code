"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from engspec_code.parser.sync import SyncReport, sync_check


def _write_engspec(path: Path, source_path: str) -> None:
    """
    Write a minimal .engspec file.
    """
    content = f"""<!-- engspec v1 -->
<!-- source: {source_path} -->
<!-- language: python -->
<!-- model: claude-opus-4-6 -->
<!-- status: skeleton -->

## `dummy() -> None`

### Purpose
A dummy function.

### Context
- Called by:
- Calls:
- Test coverage: none

### Preconditions
<!-- TO BE FILLED BY AGENT -->

### Postconditions
<!-- TO BE FILLED BY AGENT -->

---
"""
    path.write_text(content, encoding="utf-8")


def test_sync_covered():
    """
    Test that matching source and engspec files are reported
    as covered.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / "src"
        esp_dir = Path(tmpdir) / "engspec"
        src_dir.mkdir()
        esp_dir.mkdir()

        # Create source file
        src_file = src_dir / "module.py"
        src_file.write_text("def foo(): pass\n", encoding="utf-8")

        # Create matching engspec
        esp_file = esp_dir / "module.engspec"
        _write_engspec(esp_file, "module.py")

        report = sync_check(src_dir, esp_dir)

        assert "module.py" in report.covered_functions
        assert len(report.orphaned_specs) == 0
        assert len(report.stale_specs) == 0
        assert len(report.uncovered_functions) == 0


def test_sync_uncovered():
    """
    Test that source files without engspec are reported as uncovered.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / "src"
        esp_dir = Path(tmpdir) / "engspec"
        src_dir.mkdir()
        esp_dir.mkdir()

        # Create source file with no matching engspec
        src_file = src_dir / "new_module.py"
        src_file.write_text("def bar(): pass\n", encoding="utf-8")

        report = sync_check(src_dir, esp_dir)

        assert "new_module.py" in report.uncovered_functions


def test_sync_orphaned():
    """
    Test that engspec files without matching source are reported
    as orphaned.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / "src"
        esp_dir = Path(tmpdir) / "engspec"
        src_dir.mkdir()
        esp_dir.mkdir()

        # Create engspec with no matching source
        esp_file = esp_dir / "deleted.engspec"
        _write_engspec(esp_file, "deleted.py")

        report = sync_check(src_dir, esp_dir)

        assert "deleted.py" in report.orphaned_specs


def test_sync_empty_dirs():
    """
    Test sync_check with empty directories.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / "src"
        esp_dir = Path(tmpdir) / "engspec"
        src_dir.mkdir()
        esp_dir.mkdir()

        report = sync_check(src_dir, esp_dir)

        assert report == SyncReport()
