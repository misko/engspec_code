"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from engspec_code.callgraph.graph import CallGraph
from engspec_code.parser.engspec_file import EngspecFile


def build_call_graph(engspec_files: list[EngspecFile]) -> CallGraph:
    """
    Build a CallGraph from the Context sections of .engspec files.

    Args:
        engspec_files: List of parsed EngspecFile instances.

    Returns:
        A CallGraph with nodes and edges derived from
        called_by/calls relationships.
    """
    graph = CallGraph()

    # Collect all specs from all files
    for ef in engspec_files:
        for func_name, spec in ef.specs.items():
            graph.nodes[func_name] = spec

    # Build edges from context
    for func_name, spec in graph.nodes.items():
        for callee in spec.context.calls:
            # Normalize callee name (strip self. prefix etc.)
            callee_name = _normalize_name(callee)
            graph.edges.append((func_name, callee_name))

        for caller in spec.context.called_by:
            caller_name = _normalize_name(caller)
            # caller -> this function
            graph.edges.append((caller_name, func_name))

    # Deduplicate edges
    graph.edges = list(set(graph.edges))

    return graph


def _normalize_name(name: str) -> str:
    """
    Normalize a function reference name.

    Strips common prefixes like 'self.' and extracts
    the base function name.

    Args:
        name: Raw function reference from context.

    Returns:
        Normalized function name.
    """
    name = name.strip()
    # Extract the last component for qualified names
    # e.g. "ClassName.method()" -> "method"
    if "." in name:
        parts = name.split(".")
        name = parts[-1]
    # Remove trailing parentheses
    name = name.rstrip("()")
    return name
