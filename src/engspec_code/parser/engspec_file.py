"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ContextInfo:
    """
    Context information about a function's relationships.
    """

    called_by: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    test_coverage: str = ""


@dataclass
class DebateEntry:
    """
    A single entry in a spec's debate log.
    """

    round: int
    agent: str
    finding: str
    ruling: str
    action: str


@dataclass
class EngSpec:
    """
    Specification for a single function.
    """

    function_signature: str
    purpose: str = ""
    context: ContextInfo = field(default_factory=ContextInfo)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    test_strategy: list[str] = field(default_factory=list)
    debate_log: list[DebateEntry] = field(default_factory=list)


@dataclass
class EngspecFile:
    """
    A complete .engspec file containing specs for all functions
    in a source file.
    """

    source_path: str
    language: str
    model: str = ""
    status: str = "skeleton"
    validated: datetime | None = None
    regeneration_count: int = 0
    regeneration_pass_rate: str = ""
    specs: dict[str, EngSpec] = field(default_factory=dict)

    @classmethod
    def parse(cls, path: str | Path) -> EngspecFile:
        """
        Parse a markdown .engspec file into an EngspecFile.

        Args:
            path: Path to the .engspec file.

        Returns:
            Parsed EngspecFile instance.
        """
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return cls._parse_text(text)

    @classmethod
    def _parse_text(cls, text: str) -> EngspecFile:
        """
        Parse .engspec markdown text into an EngspecFile.

        Args:
            text: Raw markdown text content.

        Returns:
            Parsed EngspecFile instance.
        """
        metadata = _parse_metadata(text)
        source_path = metadata.get("source", "")
        language = metadata.get("language", "")
        model = metadata.get("model", "")
        status = metadata.get("status", "skeleton")

        validated = None
        if metadata.get("validated"):
            try:
                validated = datetime.fromisoformat(
                    metadata["validated"].replace("Z", "+00:00")
                )
            except ValueError:
                validated = None

        regen_count = 0
        if metadata.get("regeneration_count"):
            try:
                regen_count = int(metadata["regeneration_count"])
            except ValueError:
                regen_count = 0

        regen_rate = metadata.get("regeneration_pass_rate", "")

        specs = _parse_specs(text)

        return cls(
            source_path=source_path,
            language=language,
            model=model,
            status=status,
            validated=validated,
            regeneration_count=regen_count,
            regeneration_pass_rate=regen_rate,
            specs=specs,
        )

    def serialize(self) -> str:
        """
        Serialize this EngspecFile back to markdown format.

        Returns:
            Markdown string in .engspec format.
        """
        lines: list[str] = []

        # Metadata comments
        lines.append("<!-- engspec v1 -->")
        lines.append(f"<!-- source: {self.source_path} -->")
        lines.append(f"<!-- language: {self.language} -->")
        lines.append(f"<!-- model: {self.model} -->")
        lines.append(f"<!-- status: {self.status} -->")

        if self.validated is not None:
            ts = self.validated.strftime("%Y-%m-%dT%H:%M:%SZ")
            lines.append(f"<!-- validated: {ts} -->")

        if self.regeneration_count > 0:
            lines.append(
                f"<!-- regeneration_count: {self.regeneration_count} -->"
            )

        if self.regeneration_pass_rate:
            lines.append(
                f"<!-- regeneration_pass_rate:"
                f" {self.regeneration_pass_rate} -->"
            )

        lines.append("")

        for _name, spec in self.specs.items():
            lines.append(_serialize_spec(spec))

        return "\n".join(lines)


def _parse_metadata(text: str) -> dict[str, str]:
    """
    Extract HTML comment metadata from .engspec text.

    Args:
        text: Raw .engspec markdown text.

    Returns:
        Dictionary of metadata key-value pairs.
    """
    metadata: dict[str, str] = {}
    pattern = re.compile(r"<!--\s*(\S+?):\s*(.*?)\s*-->")
    for match in pattern.finditer(text):
        key = match.group(1)
        value = match.group(2)
        if key != "engspec":
            metadata[key] = value
    return metadata


def _parse_specs(text: str) -> dict[str, EngSpec]:
    """
    Parse all function spec sections from .engspec text.

    Args:
        text: Raw .engspec markdown text.

    Returns:
        Dictionary mapping function names to EngSpec instances.
    """
    specs: dict[str, EngSpec] = {}

    # Split on ## ` to find function sections
    # Each section starts with ## `signature`
    sig_pattern = re.compile(r"^## `(.+?)`\s*$", re.MULTILINE)
    matches = list(sig_pattern.finditer(text))

    for i, match in enumerate(matches):
        signature = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]

        spec = _parse_single_spec(signature, section_text)

        # Extract function name from signature
        func_name = _extract_func_name(signature)
        specs[func_name] = spec

    return specs


def _extract_func_name(signature: str) -> str:
    """
    Extract the function name from a signature string.

    Args:
        signature: Function signature like "foo(x: int) -> str".

    Returns:
        The function name, e.g. "foo".
    """
    # Handle method signatures like "self.method(...)"
    # and plain function signatures like "func(...)"
    match = re.match(r"(?:\w+\.)*(\w+)\s*\(", signature)
    if match:
        return match.group(1)
    return signature.strip()


def _parse_single_spec(signature: str, text: str) -> EngSpec:
    """
    Parse a single function's spec sections.

    Args:
        signature: The function signature.
        text: The markdown text for this function's sections.

    Returns:
        An EngSpec instance.
    """
    spec = EngSpec(function_signature=signature)

    sections = _split_sections(text)

    spec.purpose = sections.get("Purpose", "").strip()

    context_text = sections.get("Context", "")
    spec.context = _parse_context(context_text)

    spec.preconditions = _parse_bullet_list(
        sections.get("Preconditions", "")
    )
    spec.postconditions = _parse_bullet_list(
        sections.get("Postconditions", "")
    )
    spec.invariants = _parse_bullet_list(sections.get("Invariants", ""))
    spec.implementation_notes = _parse_bullet_list(
        sections.get("Implementation Notes", "")
    )
    spec.failure_modes = _parse_bullet_list(
        sections.get("Failure Modes", "")
    )
    spec.test_strategy = _parse_bullet_list(
        sections.get("Test Strategy", "")
    )
    spec.debate_log = _parse_debate_log(sections.get("Debate Log", ""))

    return spec


def _split_sections(text: str) -> dict[str, str]:
    """
    Split markdown text into sections by ### headers.

    Args:
        text: Markdown text containing ### sections.

    Returns:
        Dictionary mapping section names to their content.
    """
    sections: dict[str, str] = {}
    header_pattern = re.compile(r"^### (.+)$", re.MULTILINE)
    matches = list(header_pattern.finditer(text))

    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Strip HTML comment placeholders
        content = re.sub(
            r"<!--\s*TO BE FILLED BY AGENT\s*-->", "", content
        ).strip()
        sections[name] = content

    return sections


def _parse_context(text: str) -> ContextInfo:
    """
    Parse a Context section into a ContextInfo.

    Args:
        text: Text content of the Context section.

    Returns:
        Parsed ContextInfo instance.
    """
    ctx = ContextInfo()

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- Called by:"):
            items = line[len("- Called by:") :].strip()
            ctx.called_by = [
                s.strip() for s in items.split(",") if s.strip()
            ]
        elif line.startswith("- Calls:"):
            items = line[len("- Calls:") :].strip()
            ctx.calls = [
                s.strip() for s in items.split(",") if s.strip()
            ]
        elif line.startswith("- Test coverage:"):
            ctx.test_coverage = line[len("- Test coverage:") :].strip()

    return ctx


def _parse_bullet_list(text: str) -> list[str]:
    """
    Parse a markdown bullet list into a list of strings.

    Args:
        text: Markdown text with bullet points.

    Returns:
        List of bullet point strings (without the leading dash).
    """
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _parse_debate_log(text: str) -> list[DebateEntry]:
    """
    Parse a markdown table debate log.

    Args:
        text: Markdown table text for the debate log.

    Returns:
        List of DebateEntry instances.
    """
    entries: list[DebateEntry] = []

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip header and separator rows
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        if cells[0] in ("Round", "-----", "-------", "---"):
            continue
        if all(c.startswith("-") for c in cells):
            continue

        try:
            entry = DebateEntry(
                round=int(cells[0]),
                agent=cells[1],
                finding=cells[2],
                ruling=cells[3],
                action=cells[4],
            )
            entries.append(entry)
        except (ValueError, IndexError):
            continue

    return entries


def _serialize_spec(spec: EngSpec) -> str:
    """
    Serialize a single EngSpec to markdown.

    Args:
        spec: The EngSpec to serialize.

    Returns:
        Markdown string for this spec section.
    """
    lines: list[str] = []

    lines.append(f"## `{spec.function_signature}`")
    lines.append("")

    lines.append("### Purpose")
    if spec.purpose:
        lines.append(spec.purpose)
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Context")
    if spec.context.called_by:
        called = ", ".join(spec.context.called_by)
        lines.append(f"- Called by: {called}")
    if spec.context.calls:
        calls = ", ".join(spec.context.calls)
        lines.append(f"- Calls: {calls}")
    if spec.context.test_coverage:
        lines.append(f"- Test coverage: {spec.context.test_coverage}")
    lines.append("")

    lines.append("### Preconditions")
    if spec.preconditions:
        for item in spec.preconditions:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Postconditions")
    if spec.postconditions:
        for item in spec.postconditions:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Invariants")
    if spec.invariants:
        for item in spec.invariants:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Implementation Notes")
    if spec.implementation_notes:
        for item in spec.implementation_notes:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Failure Modes")
    if spec.failure_modes:
        for item in spec.failure_modes:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Test Strategy")
    if spec.test_strategy:
        for item in spec.test_strategy:
            lines.append(f"- {item}")
    else:
        lines.append("<!-- TO BE FILLED BY AGENT -->")
    lines.append("")

    lines.append("### Debate Log")
    lines.append("| Round | Agent | Finding | Ruling | Action |")
    lines.append("|-------|-------|---------|--------|--------|")
    for entry in spec.debate_log:
        lines.append(
            f"| {entry.round} | {entry.agent} | {entry.finding}"
            f" | {entry.ruling} | {entry.action} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)
