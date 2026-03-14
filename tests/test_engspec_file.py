"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from engspec_code.parser.engspec_file import (
    ContextInfo,
    DebateEntry,
    EngSpec,
    EngspecFile,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_sample_engspec():
    """
    Test parsing the sample.engspec fixture file.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")

    assert ef.source_path == "tests/fixtures/sample.py"
    assert ef.language == "python"
    assert ef.model == "claude-opus-4-6"
    assert ef.status == "validated"
    assert ef.validated is not None
    assert ef.regeneration_count == 5
    assert ef.regeneration_pass_rate == "5/5"

    assert len(ef.specs) == 3
    assert "add" in ef.specs
    assert "divide" in ef.specs
    assert "compute" in ef.specs


def test_parse_spec_details():
    """
    Test that parsed spec details are correct.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")

    add_spec = ef.specs["add"]
    assert add_spec.function_signature == "add(a: int, b: int) -> int"
    assert "Add two integers" in add_spec.purpose
    assert "Calculator.compute()" in add_spec.context.called_by
    assert len(add_spec.preconditions) == 1
    assert len(add_spec.postconditions) == 2
    assert len(add_spec.invariants) == 1
    assert len(add_spec.test_strategy) == 3


def test_parse_context():
    """
    Test parsing the Context section.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")

    compute_spec = ef.specs["compute"]
    assert compute_spec.context.calls == ["divide()"]
    assert compute_spec.context.test_coverage == "not yet tested"


def test_parse_no_debate_log():
    """
    Test that specs without a Debate Log section parse correctly.

    Debate Log is added by engspec_tester, not during code→engspec.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")

    for spec in ef.specs.values():
        assert len(spec.debate_log) == 0


def test_serialize_roundtrip():
    """
    Test that parse -> serialize -> parse produces equivalent data.
    """
    ef = EngspecFile.parse(FIXTURES_DIR / "sample.engspec")
    serialized = ef.serialize()

    # Parse the serialized output
    ef2 = EngspecFile._parse_text(serialized)

    assert ef2.source_path == ef.source_path
    assert ef2.language == ef.language
    assert ef2.model == ef.model
    assert ef2.status == ef.status
    assert ef2.regeneration_count == ef.regeneration_count
    assert ef2.regeneration_pass_rate == ef.regeneration_pass_rate

    assert len(ef2.specs) == len(ef.specs)
    for name in ef.specs:
        assert name in ef2.specs
        orig = ef.specs[name]
        rt = ef2.specs[name]
        assert rt.function_signature == orig.function_signature
        assert rt.preconditions == orig.preconditions
        assert rt.postconditions == orig.postconditions
        assert rt.invariants == orig.invariants
        assert rt.failure_modes == orig.failure_modes
        assert rt.test_strategy == orig.test_strategy


def test_serialize_skeleton():
    """
    Test serializing a skeleton engspec file (with placeholders).
    """
    ef = EngspecFile(
        source_path="src/foo.py",
        language="python",
        model="claude-opus-4-6",
        status="skeleton",
        specs={
            "bar": EngSpec(
                function_signature="bar(x: int) -> str",
                purpose="Convert integer to string.",
                context=ContextInfo(
                    called_by=["main()"],
                    calls=[],
                    test_coverage="untested",
                ),
            ),
        },
    )

    text = ef.serialize()

    assert "<!-- source: src/foo.py -->" in text
    assert "<!-- status: skeleton -->" in text
    assert "## `bar(x: int) -> str`" in text
    assert "Convert integer to string." in text
    assert "- Called by: main()" in text
    assert "<!-- TO BE FILLED BY AGENT -->" in text
    # No validated timestamp for skeleton
    assert "<!-- validated:" not in text


def test_construct_engspec_manually():
    """
    Test constructing an EngSpec manually and serializing it.
    """
    spec = EngSpec(
        function_signature="greet(name: str) -> str",
        purpose="Return a greeting string.",
        context=ContextInfo(
            called_by=["cli()"],
            calls=["format_name()"],
            test_coverage="tested in test_greet.py",
        ),
        preconditions=["name is a non-empty string"],
        postconditions=["Returns 'Hello, <name>!'"],
        invariants=["Pure function"],
        implementation_notes=["Uses f-string formatting"],
        failure_modes=["Empty name produces 'Hello, !'"],
        test_strategy=["Test with various name lengths"],
        debate_log=[
            DebateEntry(
                round=1,
                agent="filler",
                finding="No empty check",
                ruling="deferred",
                action="None",
            ),
        ],
    )

    ef = EngspecFile(
        source_path="greet.py",
        language="python",
        model="claude-opus-4-6",
        status="validated",
        validated=datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc),
        regeneration_count=3,
        regeneration_pass_rate="3/3",
        specs={"greet": spec},
    )

    text = ef.serialize()
    ef2 = EngspecFile._parse_text(text)

    assert ef2.specs["greet"].preconditions == [
        "name is a non-empty string"
    ]
    assert len(ef2.specs["greet"].debate_log) == 1
    assert ef2.specs["greet"].debate_log[0].round == 1
