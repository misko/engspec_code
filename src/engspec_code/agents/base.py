"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engspec_code.config import AgentConfig


class BaseAgent(ABC):
    """
    Abstract base class for Claude-powered agents.

    Provides common Claude API integration and message handling.
    """

    def __init__(self, config: AgentConfig) -> None:
        """
        Initialize the agent with configuration.

        Args:
            config: Agent configuration with model, tokens, etc.
        """
        self.config = config
        self._client = None

    def _get_client(self):
        """
        Lazily initialize the Anthropic client.

        Returns:
            Anthropic client instance.

        Raises:
            NotImplementedError: When anthropic is not installed
                or API key is not set.
        """
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic()
            except Exception as e:
                raise NotImplementedError(
                    f"Claude API client initialization failed: {e}"
                ) from e
        return self._client

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """
        Make a synchronous call to Claude.

        Args:
            system_prompt: The system prompt.
            user_message: The user message.

        Returns:
            Claude's response text.

        Raises:
            NotImplementedError: When API is not available.
        """
        client = self._get_client()
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    @abstractmethod
    def run(self, **kwargs) -> dict:
        """
        Execute the agent's primary task.

        Returns:
            Dictionary with agent results.
        """
