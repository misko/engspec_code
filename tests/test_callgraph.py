"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path

from engspec_code.callgraph.builder import build_call_graph
from engspec_code.callgraph.composition import (
    CompositionIssue,
    check_composition,
)
from engspec_code.callgraph.graph import CallGraph
from engspec_code.parser.engspec_file import (
    ContextInfo,
    EngSpec,
    EngspecFile,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_spec(
    sig: str,
    calls: list[str] | None = None,
    called_by: list[str] | None = None,
    preconditions: list[str] | None = None,
    postconditions: list[str] | None = None,
) -> EngSpec:
    """
    Helper to create an EngSpec for testing.
    """
    return EngSpec(
        function_signature=sig,
        purpose="test",
        context=ContextInfo(
            called_by=called_by or [],
            calls=calls or [],
            test_coverage="",
        ),
        preconditions=preconditions or [],
        postconditions=postconditions or [],
    )


def test_build_call_graph_from_fixture():
    """
    Test building a call graph from the sample.engspec fixture.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")
    graph = build_call_graph([ef])

    assert "add" in graph.nodes
    assert "divide" in graph.nodes
    assert "compute" in graph.nodes

    # compute calls divide
    assert any(
        s == "compute" and d == "divide"
        for s, d in graph.edges
    )


def test_build_call_graph_manual():
    """
    Test building a call graph from manually constructed specs.
    """
    ef = EngspecFile(
        source_path="test.py",
        language="python",
        source_hash="",
        specs={
            "main": _make_spec("main()", calls=["process()"]),
            "process": _make_spec(
                "process(data)",
                calls=["validate()"],
                called_by=["main()"],
            ),
            "validate": _make_spec(
                "validate(data)",
                called_by=["process()"],
            ),
        },
    )

    graph = build_call_graph([ef])

    assert len(graph.nodes) == 3
    # main -> process
    assert ("main", "process") in graph.edges
    # process -> validate
    assert ("process", "validate") in graph.edges


def test_topological_order():
    """
    Test topological ordering of the call graph.
    """
    graph = CallGraph(
        nodes={
            "a": _make_spec("a()"),
            "b": _make_spec("b()"),
            "c": _make_spec("c()"),
        },
        edges=[("a", "b"), ("b", "c")],
    )

    order = graph.topological_order()
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_topological_order_with_cycle():
    """
    Test topological ordering handles cycles gracefully.
    """
    graph = CallGraph(
        nodes={
            "a": _make_spec("a()"),
            "b": _make_spec("b()"),
        },
        edges=[("a", "b"), ("b", "a")],
    )

    order = graph.topological_order()
    # Both nodes should be present even with cycle
    assert set(order) == {"a", "b"}


def test_subgraph():
    """
    Test extracting a subgraph from a root node.
    """
    graph = CallGraph(
        nodes={
            "a": _make_spec("a()"),
            "b": _make_spec("b()"),
            "c": _make_spec("c()"),
            "d": _make_spec("d()"),
        },
        edges=[("a", "b"), ("b", "c"), ("a", "d")],
    )

    sub = graph.subgraph("a", depth=1)
    assert "a" in sub.nodes
    assert "b" in sub.nodes
    assert "d" in sub.nodes
    # c is at depth 2, should not be included
    assert "c" not in sub.nodes


def test_subgraph_depth_zero():
    """
    Test subgraph with depth 0 returns only the root.
    """
    graph = CallGraph(
        nodes={
            "a": _make_spec("a()"),
            "b": _make_spec("b()"),
        },
        edges=[("a", "b")],
    )

    sub = graph.subgraph("a", depth=0)
    assert "a" in sub.nodes
    assert "b" not in sub.nodes


def test_subgraph_nonexistent_root():
    """
    Test subgraph with nonexistent root returns empty graph.
    """
    graph = CallGraph(
        nodes={"a": _make_spec("a()")},
        edges=[],
    )

    sub = graph.subgraph("nonexistent", depth=5)
    assert len(sub.nodes) == 0


def test_composition_no_issues():
    """
    Test composition check with compatible post/preconditions.
    """
    graph = CallGraph(
        nodes={
            "caller": _make_spec(
                "caller()",
                postconditions=["Returns valid data"],
            ),
            "callee": _make_spec(
                "callee(data)",
                preconditions=["data is valid"],
            ),
        },
        edges=[("caller", "callee")],
    )

    issues = check_composition(graph)
    assert len(issues) == 0


def test_composition_missing_postconditions():
    """
    Test composition check flags missing postconditions.
    """
    graph = CallGraph(
        nodes={
            "caller": _make_spec("caller()"),
            "callee": _make_spec(
                "callee(data)",
                preconditions=["data is not None"],
            ),
        },
        edges=[("caller", "callee")],
    )

    issues = check_composition(graph)
    assert len(issues) == 1
    assert issues[0].caller == "caller"
    assert issues[0].callee == "callee"


def test_composition_none_conflict():
    """
    Test composition check detects None-related conflicts.
    """
    graph = CallGraph(
        nodes={
            "producer": _make_spec(
                "producer()",
                postconditions=["Result may be None"],
            ),
            "consumer": _make_spec(
                "consumer(data)",
                preconditions=["data is not None"],
            ),
        },
        edges=[("producer", "consumer")],
    )

    issues = check_composition(graph)
    assert len(issues) >= 1
    assert any("None" in issue.issue for issue in issues)
