"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

import click


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """
    engspec: English-First Specification Layer for Any Codebase.
    """


@cli.command("create-input")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--url", default=None, help="Clone from git URL first.")
def create_input(repo_path: str, url: str | None) -> None:
    """
    Analyze a repository and generate a draft input.md.
    """
    click.echo("Not yet implemented: create-input")


@cli.command("process-input")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option(
    "--input",
    "input_path",
    default="input.md",
    help="Path to input.md.",
)
def process_input(repo_path: str, input_path: str) -> None:
    """
    Process input.md into input_processed.md and skeleton .engspec files.
    """
    click.echo("Not yet implemented: process-input")


@cli.command("bootstrap")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--input",
    "input_path",
    required=True,
    help="Path to input_processed.md.",
)
@click.option(
    "--regen-count",
    default=5,
    help="Regenerations per function.",
)
@click.option(
    "--max-iterations",
    default=5,
    help="Max spec revision rounds.",
)
@click.option(
    "--parallelism",
    default=10,
    help="Max concurrent agents.",
)
def bootstrap(
    path: str,
    input_path: str,
    regen_count: int,
    max_iterations: int,
    parallelism: int,
) -> None:
    """
    Run agent swarm to fill and verify all .engspec files.
    """
    click.echo("Not yet implemented: bootstrap")


@cli.command("sync")
@click.argument("path", type=click.Path(exists=True))
def sync(path: str) -> None:
    """
    Report orphans, uncovered functions, and stale specs.
    """
    click.echo("Not yet implemented: sync")


@cli.command("graph")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["dot", "json"]),
    default="json",
    help="Output format.",
)
def graph(path: str, output_format: str) -> None:
    """
    Build and display call graph from .engspec Context sections.
    """
    click.echo("Not yet implemented: graph")


@cli.command("compose")
@click.argument("path", type=click.Path(exists=True))
def compose(path: str) -> None:
    """
    Check postcondition-to-precondition chains.
    """
    click.echo("Not yet implemented: compose")


@cli.command("revalidate")
@click.argument("path", type=click.Path(exists=True))
def revalidate(path: str) -> None:
    """
    Re-run regeneration verification on existing .engspec files.
    """
    click.echo("Not yet implemented: revalidate")
