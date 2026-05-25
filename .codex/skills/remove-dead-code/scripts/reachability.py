#!/usr/bin/env python3
"""Compute live and dead nodes from a call graph.

Input JSON format:
{
  "nodes": ["A", "B"],
  "roots": ["A"],
  "protected": ["FrameworkHook"],
  "edges": [["A", "B"], {"caller": "B", "callee": "C"}]
}
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


def load_graph(path: Path) -> tuple[set[str], set[str], dict[str, set[str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = set(str(node) for node in data.get("nodes", []))
    roots = set(str(node) for node in data.get("roots", []))
    roots.update(str(node) for node in data.get("protected", []))
    edges: dict[str, set[str]] = defaultdict(set)

    for edge in data.get("edges", []):
        caller: Any = None
        callee: Any = None
        if isinstance(edge, dict):
            caller = edge.get("caller")
            callee = edge.get("callee")
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            caller, callee = edge[0], edge[1]
        if caller is None or callee is None:
            continue
        caller_s = str(caller)
        callee_s = str(callee)
        nodes.add(caller_s)
        nodes.add(callee_s)
        edges[caller_s].add(callee_s)

    nodes.update(roots)
    return nodes, roots, edges


def reachable(roots: set[str], edges: dict[str, set[str]]) -> set[str]:
    live: set[str] = set()
    queue = deque(sorted(roots))
    while queue:
        node = queue.popleft()
        if node in live:
            continue
        live.add(node)
        for callee in sorted(edges.get(node, ())):
            if callee not in live:
                queue.append(callee)
    return live


def tarjan(nodes: set[str], edges: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for callee in sorted(edges.get(node, ())):
            if callee not in nodes:
                continue
            if callee not in indexes:
                visit(callee)
                lowlinks[node] = min(lowlinks[node], lowlinks[callee])
            elif callee in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[callee])

        if lowlinks[node] == indexes[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indexes:
            visit(node)
    return components


def delete_components(dead: set[str], edges: dict[str, set[str]]) -> list[list[str]]:
    components = tarjan(dead, edges)
    comp_by_node = {node: i for i, comp in enumerate(components) for node in comp}
    indegree = {i: 0 for i in range(len(components))}
    comp_edges: dict[int, set[int]] = defaultdict(set)

    for caller in dead:
        for callee in edges.get(caller, ()):
            if callee not in dead:
                continue
            caller_comp = comp_by_node[caller]
            callee_comp = comp_by_node[callee]
            if caller_comp == callee_comp:
                continue
            if callee_comp not in comp_edges[caller_comp]:
                comp_edges[caller_comp].add(callee_comp)
                indegree[callee_comp] += 1

    queue = deque(sorted(i for i, degree in indegree.items() if degree == 0))
    ordered: list[list[str]] = []
    while queue:
        comp_id = queue.popleft()
        ordered.append(components[comp_id])
        for next_id in sorted(comp_edges.get(comp_id, ())):
            indegree[next_id] -= 1
            if indegree[next_id] == 0:
                queue.append(next_id)

    if len(ordered) != len(components):
        remaining = [components[i] for i in sorted(set(range(len(components))) - {comp_by_node[n] for comp in ordered for n in comp})]
        ordered.extend(remaining)
    return ordered


def write_markdown(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Reachability",
        "",
        f"- Roots: {len(result['roots'])}",
        f"- Live nodes: {len(result['live'])}",
        f"- Dead nodes: {len(result['dead'])}",
        "",
        "## Delete Order",
        "",
    ]
    for i, comp in enumerate(result["delete_order"], start=1):
        lines.append(f"{i}. " + ", ".join(f"`{node}`" for node in comp))
    lines.extend(["", "## Dead Nodes", ""])
    for node in result["dead"]:
        lines.append(f"- `{node}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="Call graph JSON")
    parser.add_argument("--output", help="JSON output path")
    parser.add_argument("--markdown", help="Optional Markdown output path")
    args = parser.parse_args()

    nodes, roots, edges = load_graph(Path(args.graph))
    live = reachable(roots, edges)
    dead = nodes - live
    result = {
        "roots": sorted(roots),
        "live": sorted(live),
        "dead": sorted(dead),
        "delete_order": delete_components(dead, edges),
    }

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.markdown:
        write_markdown(result, Path(args.markdown))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
