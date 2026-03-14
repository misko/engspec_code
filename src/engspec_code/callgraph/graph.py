"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from engspec_code.parser.engspec_file import EngSpec


@dataclass
class CallGraph:
    """
    A directed call graph built from .engspec Context sections.
    """

    nodes: dict[str, EngSpec] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def subgraph(self, root: str, depth: int) -> CallGraph:
        """
        Extract a subgraph rooted at a given node up to a depth.

        Args:
            root: The root node name.
            depth: Maximum traversal depth.

        Returns:
            A new CallGraph containing only reachable nodes
            within the given depth.
        """
        if root not in self.nodes:
            return CallGraph()

        # Build adjacency list
        adj: dict[str, list[str]] = {}
        for src, dst in self.edges:
            adj.setdefault(src, []).append(dst)

        # BFS
        visited: dict[str, int] = {root: 0}
        queue: deque[tuple[str, int]] = deque([(root, 0)])

        while queue:
            node, d = queue.popleft()
            if d >= depth:
                continue
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited[neighbor] = d + 1
                    queue.append((neighbor, d + 1))

        sub_nodes = {
            name: self.nodes[name]
            for name in visited
            if name in self.nodes
        }
        sub_edges = [
            (s, d) for s, d in self.edges
            if s in visited and d in visited
        ]

        return CallGraph(nodes=sub_nodes, edges=sub_edges)

    def topological_order(self) -> list[str]:
        """
        Return nodes in topological order (dependencies first).

        Returns:
            List of node names in topological order.
            If the graph has cycles, returns a best-effort ordering.
        """
        # Kahn's algorithm
        in_degree: dict[str, int] = {name: 0 for name in self.nodes}
        adj: dict[str, list[str]] = {name: [] for name in self.nodes}

        for src, dst in self.edges:
            if src in self.nodes and dst in self.nodes:
                adj[src].append(dst)
                in_degree[dst] = in_degree.get(dst, 0) + 1

        queue: deque[str] = deque(
            name for name, deg in in_degree.items() if deg == 0
        )
        result: list[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If there are cycles, add remaining nodes
        remaining = [n for n in self.nodes if n not in result]
        result.extend(remaining)

        return result
