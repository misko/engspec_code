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
    from engspec_code.config import AgentConfig
    from engspec_code.parser.engspec_file import EngspecFile


class SpecFillerAgent(BaseAgent):
    """
    Agent that fills skeleton .engspec files with full specifications.

    Reads the skeleton .engspec, the corresponding source file,
    and input_processed.md, then fills in all placeholder sections.
    """

    def __init__(
        self,
        config: AgentConfig,
        processed_input_path: Path,
    ) -> None:
        """
        Initialize the spec filler agent.

        Args:
            config: Agent configuration.
            processed_input_path: Path to input_processed.md.
        """
        super().__init__(config)
        self.processed_input_path = processed_input_path
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        Load the spec filler prompt template.

        Returns:
            Prompt template string.
        """
        prompt_path = (
            Path(__file__).parent.parent / "prompts" / "spec_filler.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "Fill in the skeleton .engspec with full specifications."

    def run(
        self,
        engspec_file: EngspecFile | None = None,
        source_path: Path | None = None,
        **kwargs,
    ) -> dict:
        """
        Fill a skeleton .engspec with full specifications.

        Args:
            engspec_file: The skeleton EngspecFile to fill.
            source_path: Path to the corresponding source file.

        Returns:
            Dictionary with "engspec_file" key containing the
            filled EngspecFile.

        Raises:
            NotImplementedError: Claude API not yet integrated.
        """
        raise NotImplementedError(
            "SpecFillerAgent.run requires Claude API integration"
        )
