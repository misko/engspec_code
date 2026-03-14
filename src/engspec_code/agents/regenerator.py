"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from engspec_code.agents.base import BaseAgent

if TYPE_CHECKING:
    from engspec_code.config import AgentConfig
    from engspec_code.parser.engspec_file import EngSpec


@dataclass
class RegenerationResult:
    """
    Result of a single regeneration attempt.
    """

    attempt: int
    generated_code: str
    language: str
    properties_matched: list[str] = field(default_factory=list)
    properties_missing: list[str] = field(default_factory=list)
    passed: bool = False


class RegeneratorAgent(BaseAgent):
    """
    Agent that re-implements a function from its spec alone.

    The regenerator sees ONLY the .engspec specification (no source
    code) and produces an implementation. This tests whether the
    spec is complete enough for faithful reproduction.
    """

    def __init__(self, config: AgentConfig) -> None:
        """
        Initialize the regenerator agent.

        Args:
            config: Agent configuration.
        """
        super().__init__(config)
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        Load the regenerator prompt template.

        Returns:
            Prompt template string.
        """
        prompt_path = (
            Path(__file__).parent.parent / "prompts" / "regenerator.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "Re-implement this function from the spec alone."

    def run(
        self,
        spec: EngSpec | None = None,
        language: str = "python",
        **kwargs,
    ) -> dict:
        """
        Regenerate a function implementation from spec only.

        Args:
            spec: The EngSpec to implement from.
            language: Target language for the implementation.

        Returns:
            Dictionary with "result" key containing a
            RegenerationResult.

        Raises:
            NotImplementedError: Claude API not yet integrated.
        """
        raise NotImplementedError(
            "RegeneratorAgent.run requires Claude API integration"
        )
