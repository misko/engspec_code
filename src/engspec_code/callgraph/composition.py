"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engspec_code.callgraph.graph import CallGraph


@dataclass
class CompositionIssue:
    """
    An issue found during postcondition-to-precondition
    chain verification.
    """

    caller: str
    callee: str
    issue: str


def check_composition(graph: CallGraph) -> list[CompositionIssue]:
    """
    Verify postcondition-to-precondition chains in a call graph.

    For each edge (caller -> callee), checks that the caller's
    postconditions are compatible with the callee's preconditions.
    Reports issues where a callee has preconditions but the caller
    has no postconditions that could satisfy them.

    Args:
        graph: The CallGraph to check.

    Returns:
        List of CompositionIssue instances describing problems.
    """
    issues: list[CompositionIssue] = []

    for caller_name, callee_name in graph.edges:
        caller_spec = graph.nodes.get(caller_name)
        callee_spec = graph.nodes.get(callee_name)

        if caller_spec is None or callee_spec is None:
            # Skip edges where one side is unknown
            continue

        # If the callee has preconditions but the caller has
        # no postconditions, flag as potential issue
        if callee_spec.preconditions and not caller_spec.postconditions:
            issues.append(
                CompositionIssue(
                    caller=caller_name,
                    callee=callee_name,
                    issue=(
                        f"Callee '{callee_name}' has"
                        f" {len(callee_spec.preconditions)}"
                        f" precondition(s) but caller"
                        f" '{caller_name}' has no postconditions"
                    ),
                )
            )

        # Check for obvious mismatches: callee precondition
        # mentions something that conflicts with caller postcondition
        if caller_spec.postconditions and callee_spec.preconditions:
            caller_post_text = " ".join(
                caller_spec.postconditions
            ).lower()
            for pre in callee_spec.preconditions:
                pre_lower = pre.lower()
                # Flag if precondition mentions "not None" or
                # "non-empty" but caller postcondition mentions
                # "may be None" or "may be empty"
                if (
                    "none" in pre_lower
                    and "may be none" in caller_post_text
                ):
                    issues.append(
                        CompositionIssue(
                            caller=caller_name,
                            callee=callee_name,
                            issue=(
                                f"Callee precondition '{pre}'"
                                f" may conflict with caller"
                                f" postcondition mentioning"
                                f" 'may be None'"
                            ),
                        )
                    )

    return issues
