"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from engspec_code.agents.base import BaseAgent

if TYPE_CHECKING:
    from engspec_code.agents.regenerator import RegenerationResult
    from engspec_code.config import AgentConfig
    from engspec_code.parser.engspec_file import EngSpec


class ValidatorAgent(BaseAgent):
    """
    Agent that compares a regenerated implementation against
    the original source code.

    Checks whether the regeneration preserves all essential
    properties: preconditions, postconditions, failure modes,
    and core algorithmic behavior.
    """

    def __init__(self, config: AgentConfig) -> None:
        """
        Initialize the validator agent.

        Args:
            config: Agent configuration.
        """
        super().__init__(config)
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        Load the validator prompt template.

        Returns:
            Prompt template string.
        """
        prompt_path = (
            Path(__file__).parent.parent / "prompts" / "validator.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "Compare the regeneration against the original."

    def run(
        self,
        spec: EngSpec | None = None,
        original_source: str = "",
        regeneration: RegenerationResult | None = None,
        **kwargs,
    ) -> dict:
        """
        Compare a regeneration against the original source.

        Args:
            spec: The EngSpec being validated.
            original_source: The original source code.
            regeneration: The regenerated implementation.

        Returns:
            Dictionary with "passed" bool and "gaps" list
            of missing properties.

        Raises:
            NotImplementedError: Claude API not yet integrated.
        """
        raise NotImplementedError(
            "ValidatorAgent.run requires Claude API integration"
        )
