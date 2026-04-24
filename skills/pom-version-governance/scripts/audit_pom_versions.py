#!/usr/bin/env python3
"""Audit duplicated and conflicting Maven dependency definitions."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from xml.etree import ElementTree as ET


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
MAVEN_LOG_PREFIX_RE = re.compile(r"^\[(?:INFO|WARNING|ERROR|DEBUG)\]\s*")
MODULE_HEADER_RE = re.compile(r"--- .* @ (?P<module>[^ ]+) ---")
TREE_NODE_RE = re.compile(
    r"^(?P<prefix>(?:\|  |   )*)(?P<branch>\+-|\\-)?\s*(?P<body>.+)$"
)


@dataclass
class VersionEntry:
    kind: str
    key: str
    value: str
    pom: str
    module: str
    section: str


@dataclass
class DeclaredDependency:
    key: str
    value: str
    scope: str
    module: str
    pom: str
    section: str


@dataclass
class PomParseResult:
    module: str
    module_key: str
    rel_pom: str
    entries: List[VersionEntry]
    declared_dependencies: List[DeclaredDependency]


@dataclass
class DependencyPathEntry:
    key: str
    value: str
    module: str
    pom: str
    scope: str
    direct: bool
    path: str
    introduced_by: str
    note: str


@dataclass
class TransitiveScanResult:
    mode: str
    executed: bool
    succeeded: bool
    mvn_bin: str
    error: str
    resolved_entries: List[DependencyPathEntry]
    conflict_hint_entries: List[DependencyPathEntry]


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def child_text(elem: ET.Element | None, name: str) -> str:
    if elem is None:
        return ""
    for child in list(elem):
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def child_element(elem: ET.Element | None, name: str) -> ET.Element | None:
    if elem is None:
        return None
    for child in list(elem):
        if local_name(child.tag) == name:
            return child
    return None


def children(elem: ET.Element | None, name: str) -> Iterable[ET.Element]:
    if elem is None:
        return []
    return [child for child in list(elem) if local_name(child.tag) == name]


def build_artifact_key(group_id: str, artifact_id: str) -> str:
    return f"{group_id}:{artifact_id}" if group_id else artifact_id


def parse_declared_dependency(
    dep: ET.Element, rel_pom: str, module: str, section: str
) -> DeclaredDependency | None:
    group_id = child_text(dep, "groupId")
    artifact_id = child_text(dep, "artifactId")
    if not group_id or not artifact_id:
        return None

    return DeclaredDependency(
        key=build_artifact_key(group_id, artifact_id),
        value=child_text(dep, "version"),
        scope=child_text(dep, "scope"),
        module=module,
        pom=rel_pom,
        section=section,
    )


def parse_version_dependency(
    dep: ET.Element, rel_pom: str, module: str, section: str
) -> List[VersionEntry]:
    declared = parse_declared_dependency(dep, rel_pom, module, section)
    if declared is None or not declared.value:
        return []

    section_label = section if not declared.scope else f"{section} (scope={declared.scope})"
    return [
        VersionEntry(
            kind="dependency",
            key=declared.key,
            value=declared.value,
            pom=declared.pom,
            module=declared.module,
            section=section_label,
        )
    ]


def parse_plugin(
    plugin: ET.Element, rel_pom: str, module: str, section: str
) -> VersionEntry | None:
    group_id = child_text(plugin, "groupId") or "org.apache.maven.plugins"
    artifact_id = child_text(plugin, "artifactId")
    version = child_text(plugin, "version")

    if not artifact_id or not version:
        return None

    return VersionEntry(
        kind="plugin",
        key=build_artifact_key(group_id, artifact_id),
        value=version,
        pom=rel_pom,
        module=module,
        section=section,
    )


def parse_pom(pom_path: Path, root_dir: Path) -> PomParseResult:
    rel_pom = str(pom_path.relative_to(root_dir))
    fallback_module = pom_path.parent.name
    entries: List[VersionEntry] = []
    declared_dependencies: List[DeclaredDependency] = []

    try:
        tree = ET.parse(pom_path)
    except ET.ParseError as exc:
        print(f"[WARN] Failed to parse {pom_path}: {exc}", file=sys.stderr)
        return PomParseResult(
            module=fallback_module,
            module_key=fallback_module,
            rel_pom=rel_pom,
            entries=entries,
            declared_dependencies=declared_dependencies,
        )

    root = tree.getroot()
    parent = child_element(root, "parent")
    group_id = child_text(root, "groupId") or child_text(parent, "groupId")
    artifact_id = child_text(root, "artifactId") or fallback_module
    module = artifact_id
    module_key = build_artifact_key(group_id, artifact_id)

    properties = child_element(root, "properties")
    if properties is not None:
        for prop in list(properties):
            key = local_name(prop.tag)
            value = (prop.text or "").strip()
            if not value:
                continue
            entries.append(
                VersionEntry(
                    kind="property",
                    key=key,
                    value=value,
                    pom=rel_pom,
                    module=module,
                    section="properties",
                )
            )

    dep_mgmt = child_element(root, "dependencyManagement")
    dep_mgmt_dependencies = child_element(dep_mgmt, "dependencies")
    for dep in children(dep_mgmt_dependencies, "dependency"):
        entries.extend(parse_version_dependency(dep, rel_pom, module, "dependencyManagement"))

    direct_dependencies = child_element(root, "dependencies")
    for dep in children(direct_dependencies, "dependency"):
        declared = parse_declared_dependency(dep, rel_pom, module, "dependencies")
        if declared is not None:
            declared_dependencies.append(declared)
        entries.extend(parse_version_dependency(dep, rel_pom, module, "dependencies"))

    build = child_element(root, "build")
    plugin_mgmt = child_element(build, "pluginManagement")
    plugin_mgmt_plugins = child_element(plugin_mgmt, "plugins")
    for plugin in children(plugin_mgmt_plugins, "plugin"):
        plugin_entry = parse_plugin(plugin, rel_pom, module, "pluginManagement")
        if plugin_entry:
            entries.append(plugin_entry)

    plugins = child_element(build, "plugins")
    for plugin in children(plugins, "plugin"):
        plugin_entry = parse_plugin(plugin, rel_pom, module, "plugins")
        if plugin_entry:
            entries.append(plugin_entry)

    return PomParseResult(
        module=module,
        module_key=module_key,
        rel_pom=rel_pom,
        entries=entries,
        declared_dependencies=declared_dependencies,
    )


def find_pom_files(root_dir: Path, ignored_dirs: Sequence[str]) -> List[Path]:
    pom_files: List[Path] = []
    ignored = set(ignored_dirs)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [name for name in dirnames if name not in ignored]
        if "pom.xml" in filenames:
            pom_files.append(Path(dirpath) / "pom.xml")
    return sorted(pom_files)


def group_version_entries(entries: Iterable[VersionEntry]) -> Dict[str, List[VersionEntry]]:
    grouped: Dict[str, List[VersionEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.key].append(entry)
    return grouped


def analyze_version_groups(
    grouped: Dict[str, List[VersionEntry]], min_occurrences: int
) -> Dict[str, List[Dict[str, object]]]:
    conflicts: List[Dict[str, object]] = []
    duplicates: List[Dict[str, object]] = []

    for key, rows in grouped.items():
        if len(rows) < min_occurrences:
            continue

        value_groups: Dict[str, List[VersionEntry]] = defaultdict(list)
        for row in rows:
            value_groups[row.value].append(row)

        info = {
            "key": key,
            "occurrences": len(rows),
            "values": [
                {
                    "value": value,
                    "locations": [
                        {
                            "pom": item.pom,
                            "module": item.module,
                            "section": item.section,
                        }
                        for item in sorted(
                            items, key=lambda entry: (entry.pom, entry.module, entry.section)
                        )
                    ],
                }
                for value, items in sorted(value_groups.items(), key=lambda item: item[0])
            ],
        }

        if len(value_groups) > 1:
            conflicts.append(info)
        else:
            duplicates.append(info)

    conflicts.sort(key=lambda item: item["occurrences"], reverse=True)
    duplicates.sort(key=lambda item: item["occurrences"], reverse=True)
    return {"conflicts": conflicts, "duplicates": duplicates}


def analyze_path_entries(
    entries: Iterable[DependencyPathEntry], min_occurrences: int
) -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[DependencyPathEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.key].append(entry)

    conflicts: List[Dict[str, object]] = []
    duplicates: List[Dict[str, object]] = []

    for key, rows in grouped.items():
        if len(rows) < min_occurrences:
            continue

        value_groups: Dict[str, List[DependencyPathEntry]] = defaultdict(list)
        for row in rows:
            value_groups[row.value].append(row)

        info = {
            "key": key,
            "occurrences": len(rows),
            "values": [
                {
                    "value": value,
                    "locations": [
                        {
                            "module": item.module,
                            "pom": item.pom,
                            "scope": item.scope,
                            "relationship": "direct" if item.direct else "transitive",
                            "introduced_by": item.introduced_by,
                            "path": item.path,
                            "note": item.note,
                        }
                        for item in sorted(
                            items,
                            key=lambda entry: (
                                entry.module,
                                entry.path,
                                entry.scope,
                                entry.note,
                            ),
                        )
                    ],
                }
                for value, items in sorted(value_groups.items(), key=lambda item: item[0])
            ],
        }

        if len(value_groups) > 1:
            conflicts.append(info)
        else:
            duplicates.append(info)

    conflicts.sort(key=lambda item: item["occurrences"], reverse=True)
    duplicates.sort(key=lambda item: item["occurrences"], reverse=True)
    return {"conflicts": conflicts, "duplicates": duplicates}


def build_component_propagation_entries(
    pom_results: Sequence[PomParseResult],
) -> List[DependencyPathEntry]:
    project_module_keys = {
        result.module_key for result in pom_results if result.module_key
    }
    module_name_by_key = {
        result.module_key: result.module for result in pom_results if result.module_key
    }
    dependencies_by_module = {
        result.module_key: result.declared_dependencies
        for result in pom_results
        if result.module_key
    }

    entries: List[DependencyPathEntry] = []
    seen: set[tuple[str, str, str, str]] = set()

    for consumer in pom_results:
        queue: deque[tuple[str, List[str]]] = deque()
        for dep in consumer.declared_dependencies:
            if dep.key in project_module_keys:
                queue.append((dep.key, [dep.key]))

        while queue:
            current_key, internal_path = queue.popleft()
            for dep in dependencies_by_module.get(current_key, []):
                if dep.key == consumer.module_key:
                    continue

                path_parts = [consumer.module]
                path_parts.extend(
                    module_name_by_key.get(module_key, module_key)
                    for module_key in internal_path
                )
                path_parts.append(dep.key)

                entry = DependencyPathEntry(
                    key=dep.key,
                    value=dep.value or "(managed/implicit)",
                    module=consumer.module,
                    pom=consumer.rel_pom,
                    scope=dep.scope,
                    direct=False,
                    path=" -> ".join(path_parts),
                    introduced_by=module_name_by_key.get(
                        internal_path[0], internal_path[0]
                    ),
                    note=f"declared in {module_name_by_key.get(current_key, current_key)}",
                )

                dedupe_key = (entry.module, entry.key, entry.value, entry.path)
                if dedupe_key not in seen:
                    entries.append(entry)
                    seen.add(dedupe_key)

                if dep.key in project_module_keys and dep.key not in internal_path:
                    queue.append((dep.key, internal_path + [dep.key]))

    return entries


def discover_maven_binary(requested_mvn_bin: str) -> str:
    if requested_mvn_bin:
        return requested_mvn_bin

    discovered = shutil.which("mvn")
    if discovered:
        return discovered

    return ""


def normalize_maven_line(line: str) -> str:
    return MAVEN_LOG_PREFIX_RE.sub("", ANSI_ESCAPE_RE.sub("", line)).rstrip()


def summarize_maven_error(output: str, max_lines: int = 8) -> str:
    lines = [normalize_maven_line(line) for line in output.splitlines()]
    lines = [line for line in lines if line]
    preferred = [
        line
        for line in lines
        if (
            "BUILD FAILURE" in line
            or "No plugin found for prefix 'dependency'" in line
            or "Could not transfer metadata" in line
            or "Failed to retrieve plugin descriptor" in line
            or "Failed to create parent directories" in line
            or "Operation not permitted" in line
        )
    ]
    priority_markers = [
        "No plugin found for prefix 'dependency'",
        "BUILD FAILURE",
        "Operation not permitted",
        "Failed to retrieve plugin descriptor",
        "Could not transfer metadata",
        "Failed to create parent directories",
    ]
    selected: List[str] = []
    for marker in priority_markers:
        for line in preferred:
            if marker in line and line not in selected:
                selected.append(line)
                break

    for line in preferred or lines:
        if line not in selected:
            selected.append(line)
        if len(selected) >= max_lines:
            break

    if len(selected) > max_lines:
        selected = selected[:max_lines] + ["... (truncated)"]
    return " | ".join(selected)


def parse_tree_body(body: str) -> Dict[str, str] | None:
    note = ""
    coordinates = body.strip()

    if " (" in coordinates and coordinates.endswith(")"):
        coordinates, note = coordinates.split(" (", 1)
        coordinates = coordinates.strip()
        note = note[:-1].strip()

    parts = coordinates.split(":")
    if len(parts) < 4:
        return None

    if len(parts) == 4:
        group_id, artifact_id, _packaging, version = parts
        scope = ""
    else:
        group_id = parts[0]
        artifact_id = parts[1]
        version = parts[-2]
        scope = parts[-1]

    return {
        "group_id": group_id,
        "artifact_id": artifact_id,
        "version": version,
        "scope": scope,
        "note": note,
    }


def parse_dependency_tree_output(
    output: str, module_to_pom: Dict[str, str]
) -> tuple[List[DependencyPathEntry], List[DependencyPathEntry]]:
    resolved_entries: List[DependencyPathEntry] = []
    conflict_hint_entries: List[DependencyPathEntry] = []

    current_module = ""
    stack: List[str] = []

    for raw_line in output.splitlines():
        line = normalize_maven_line(raw_line)
        if not line:
            continue

        module_match = MODULE_HEADER_RE.search(line)
        if module_match:
            current_module = module_match.group("module")
            stack = []
            continue

        if not current_module:
            continue

        node_match = TREE_NODE_RE.match(line)
        if not node_match:
            continue

        prefix = node_match.group("prefix") or ""
        branch = node_match.group("branch")
        parsed = parse_tree_body(node_match.group("body"))
        if parsed is None:
            continue

        depth = prefix.count("|  ") + prefix.count("   ")
        if branch:
            depth += 1

        key = build_artifact_key(parsed["group_id"], parsed["artifact_id"])
        note = parsed["note"]

        if depth == 0:
            stack = [key]
            continue

        while len(stack) > depth:
            stack.pop()

        path_parts = [current_module] + stack[1:] + [key]
        entry = DependencyPathEntry(
            key=key,
            value=parsed["version"],
            module=current_module,
            pom=module_to_pom.get(current_module, ""),
            scope=parsed["scope"],
            direct=depth == 1,
            path=" -> ".join(path_parts),
            introduced_by=key if depth == 1 or len(stack) < 2 else stack[1],
            note=note,
        )

        if "omitted for conflict" in note:
            conflict_hint_entries.append(entry)
            continue

        resolved_entries.append(entry)
        if len(stack) == depth:
            stack.append(key)
        elif len(stack) < depth:
            stack.append(key)
        else:
            stack = stack[:depth] + [key]

    return resolved_entries, conflict_hint_entries


def run_transitive_scan(
    root_dir: Path, mode: str, requested_mvn_bin: str, module_to_pom: Dict[str, str]
) -> TransitiveScanResult:
    mvn_bin = discover_maven_binary(requested_mvn_bin)
    if mode == "off":
        return TransitiveScanResult(
            mode=mode,
            executed=False,
            succeeded=False,
            mvn_bin=mvn_bin,
            error="Disabled by --transitive-mode off.",
            resolved_entries=[],
            conflict_hint_entries=[],
        )

    if not mvn_bin:
        return TransitiveScanResult(
            mode=mode,
            executed=False,
            succeeded=False,
            mvn_bin="",
            error="Maven executable not found in PATH.",
            resolved_entries=[],
            conflict_hint_entries=[],
        )

    cmd = [
        mvn_bin,
        "-ntp",
        "-Dstyle.color=never",
        "-DskipTests",
        "dependency:tree",
        "-Dverbose",
    ]

    try:
        completed = subprocess.run(
            cmd,
            cwd=root_dir,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        return TransitiveScanResult(
            mode=mode,
            executed=True,
            succeeded=False,
            mvn_bin=mvn_bin,
            error=str(exc),
            resolved_entries=[],
            conflict_hint_entries=[],
        )

    if completed.returncode != 0:
        return TransitiveScanResult(
            mode=mode,
            executed=True,
            succeeded=False,
            mvn_bin=mvn_bin,
            error=summarize_maven_error(completed.stdout),
            resolved_entries=[],
            conflict_hint_entries=[],
        )

    resolved_entries, conflict_hint_entries = parse_dependency_tree_output(
        completed.stdout, module_to_pom
    )
    return TransitiveScanResult(
        mode=mode,
        executed=True,
        succeeded=True,
        mvn_bin=mvn_bin,
        error="",
        resolved_entries=resolved_entries,
        conflict_hint_entries=conflict_hint_entries,
    )


def build_report_payload(
    root_dir: Path,
    pom_files: List[Path],
    entries: List[VersionEntry],
    component_entries: List[DependencyPathEntry],
    min_occurrences: int,
    transitive_scan: TransitiveScanResult,
) -> Dict[str, object]:
    dependency_entries = [entry for entry in entries if entry.kind == "dependency"]
    plugin_entries = [entry for entry in entries if entry.kind == "plugin"]
    property_entries = [entry for entry in entries if entry.kind == "property"]

    dependencies = analyze_version_groups(
        group_version_entries(dependency_entries), min_occurrences
    )
    plugins = analyze_version_groups(
        group_version_entries(plugin_entries), min_occurrences
    )
    properties = analyze_version_groups(
        group_version_entries(property_entries), min_occurrences
    )

    component_analysis = analyze_path_entries(component_entries, min_occurrences)

    effective_dependencies = analyze_path_entries(
        transitive_scan.resolved_entries, min_occurrences
    )
    indirect_dependencies = analyze_path_entries(
        [entry for entry in transitive_scan.resolved_entries if not entry.direct],
        min_occurrences,
    )
    conflict_hints = analyze_path_entries(transitive_scan.conflict_hint_entries, 1)

    transitive_payload = {
        "mode": transitive_scan.mode,
        "executed": transitive_scan.executed,
        "succeeded": transitive_scan.succeeded,
        "mvn_bin": transitive_scan.mvn_bin,
        "error": transitive_scan.error,
        "resolved_dependency_occurrences": len(transitive_scan.resolved_entries),
        "conflict_hint_occurrences": len(transitive_scan.conflict_hint_entries),
        "effective_dependencies": effective_dependencies,
        "indirect_dependencies": indirect_dependencies,
        "conflict_hints": conflict_hints,
        "raw_resolved_entries": [asdict(entry) for entry in transitive_scan.resolved_entries],
        "raw_conflict_hint_entries": [
            asdict(entry) for entry in transitive_scan.conflict_hint_entries
        ],
    }

    component_payload = {
        "dependency_occurrences": len(component_entries),
        "dependencies": component_analysis,
        "raw_entries": [asdict(entry) for entry in component_entries],
    }

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root_dir),
        "pom_files": len(pom_files),
        "dependency_versions": len(dependency_entries),
        "plugin_versions": len(plugin_entries),
        "property_versions": len(property_entries),
        "dependency_conflicts": len(dependencies["conflicts"]),
        "plugin_conflicts": len(plugins["conflicts"]),
        "property_conflicts": len(properties["conflicts"]),
        "component_indirect_conflicts": len(component_analysis["conflicts"]),
        "transitive_scan_executed": transitive_scan.executed,
        "transitive_scan_succeeded": transitive_scan.succeeded,
        "effective_dependency_conflicts": len(effective_dependencies["conflicts"]),
        "indirect_dependency_conflicts": len(indirect_dependencies["conflicts"]),
        "transitive_conflict_hints": len(conflict_hints["conflicts"])
        + len(conflict_hints["duplicates"]),
    }

    return {
        "summary": summary,
        "dependencies": dependencies,
        "plugins": plugins,
        "properties": properties,
        "component_analysis": component_payload,
        "transitive_analysis": transitive_payload,
        "raw_entries": [asdict(entry) for entry in entries],
    }


def render_version_section(title: str, groups: Sequence[Dict[str, object]]) -> List[str]:
    lines = [f"### {title}", ""]
    if not groups:
        lines.append("- None")
        lines.append("")
        return lines

    for group in groups:
        lines.append(f"- `{group['key']}` ({group['occurrences']} occurrences)")
        for value_info in group["values"]:
            lines.append(f"  - Version/Value `{value_info['value']}`")
            for loc in value_info["locations"]:
                lines.append(
                    f"    - `{loc['pom']}` | module `{loc['module']}` | section `{loc['section']}`"
                )
        lines.append("")
    return lines


def render_path_section(
    title: str, groups: Sequence[Dict[str, object]], show_notes: bool = False
) -> List[str]:
    lines = [f"### {title}", ""]
    if not groups:
        lines.append("- None")
        lines.append("")
        return lines

    for group in groups:
        lines.append(f"- `{group['key']}` ({group['occurrences']} occurrences)")
        for value_info in group["values"]:
            lines.append(f"  - Version `{value_info['value']}`")
            for loc in value_info["locations"]:
                pom_label = loc["pom"] or "unknown pom"
                lines.append(
                    f"    - module `{loc['module']}` | {loc['relationship']} | scope `{loc['scope'] or 'n/a'}` | via `{loc['introduced_by']}` | path `{loc['path']}` | pom `{pom_label}`"
                )
                if show_notes and loc["note"]:
                    lines.append(f"      - note `{loc['note']}`")
        lines.append("")
    return lines


def render_markdown(payload: Dict[str, object], min_occurrences: int) -> str:
    summary = payload["summary"]
    component_analysis = payload["component_analysis"]
    transitive_analysis = payload["transitive_analysis"]
    lines: List[str] = []

    lines.append("# Maven POM Version Audit")
    lines.append("")
    lines.append(f"- Root: `{summary['root']}`")
    lines.append(f"- Generated (UTC): `{summary['generated_at_utc']}`")
    lines.append(f"- POM files scanned: `{summary['pom_files']}`")
    lines.append(f"- Dependency versions found: `{summary['dependency_versions']}`")
    lines.append(f"- Plugin versions found: `{summary['plugin_versions']}`")
    lines.append(f"- Property values found: `{summary['property_versions']}`")
    lines.append("")

    lines.append("## Conflicting Version Definitions")
    lines.append("")
    lines.extend(render_version_section("Dependencies", payload["dependencies"]["conflicts"]))
    lines.extend(render_version_section("Plugins", payload["plugins"]["conflicts"]))
    lines.extend(render_version_section("Properties", payload["properties"]["conflicts"]))

    lines.append("")
    lines.append(f"## Repeated Identical Definitions (>= {min_occurrences} occurrences)")
    lines.append("")
    lines.extend(render_version_section("Dependencies", payload["dependencies"]["duplicates"]))
    lines.extend(render_version_section("Plugins", payload["plugins"]["duplicates"]))
    lines.extend(render_version_section("Properties", payload["properties"]["duplicates"]))

    lines.append("")
    lines.append("## Project Component Propagation Analysis")
    lines.append("")
    lines.append(
        f"- Indirect dependency occurrences discovered through internal components: `{component_analysis['dependency_occurrences']}`"
    )
    lines.append("")
    lines.extend(
        render_path_section(
            "Indirect Version Conflicts Introduced By Project Components",
            component_analysis["dependencies"]["conflicts"],
            show_notes=True,
        )
    )
    lines.extend(
        render_path_section(
            f"Shared Indirect Dependencies Introduced By Project Components (>= {min_occurrences} occurrences)",
            component_analysis["dependencies"]["duplicates"],
            show_notes=True,
        )
    )

    lines.append("")
    lines.append("## Effective Dependency Tree Analysis")
    lines.append("")
    lines.append(f"- Mode: `{transitive_analysis['mode']}`")

    if transitive_analysis["succeeded"]:
        lines.append(
            f"- Maven tree scan: `succeeded` via `{transitive_analysis['mvn_bin']}`"
        )
        lines.append(
            f"- Resolved dependency occurrences: `{transitive_analysis['resolved_dependency_occurrences']}`"
        )
        lines.append(
            f"- Conflict hints from Maven mediation: `{transitive_analysis['conflict_hint_occurrences']}`"
        )
        lines.append("")
        lines.extend(
            render_path_section(
                "Effective Version Conflicts (Direct + Transitive)",
                transitive_analysis["effective_dependencies"]["conflicts"],
            )
        )
        lines.extend(
            render_path_section(
                "Indirect Version Conflicts From Maven Tree",
                transitive_analysis["indirect_dependencies"]["conflicts"],
            )
        )
        lines.extend(
            render_path_section(
                f"Shared Indirect Dependencies From Maven Tree (>= {min_occurrences} occurrences)",
                transitive_analysis["indirect_dependencies"]["duplicates"],
            )
        )
        lines.extend(
            render_path_section(
                "Maven Conflict Mediation Hints",
                transitive_analysis["conflict_hints"]["conflicts"]
                + transitive_analysis["conflict_hints"]["duplicates"],
                show_notes=True,
            )
        )
    else:
        status = "skipped" if not transitive_analysis["executed"] else "failed"
        lines.append(f"- Maven tree scan: `{status}`")
        lines.append(f"- Reason: `{transitive_analysis['error']}`")
        lines.append("")

    lines.append("")
    lines.append("## Consolidation Checklist")
    lines.append("")
    lines.append("1. Resolve every explicit, component-induced, or effective conflict first.")
    lines.append(
        "2. Move shared dependency versions into a root `dependencyManagement` or BOM module."
    )
    lines.append("3. Move shared plugin versions into root `pluginManagement`.")
    lines.append(
        "4. Fix indirect drift at the upstream owner when a shared SDK/starter introduces it."
    )
    lines.append(
        "5. Add exclusions only after confirming the exact path from component or Maven tree analysis."
    )
    lines.append("6. Re-run this audit and ensure conflict sections are empty.")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit duplicate/conflicting Maven dependency, plugin, property, and transitive versions."
    )
    parser.add_argument("--root", default=".", help="Project root to scan.")
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum repeat count to report duplicates/conflicts.",
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Directory names to ignore. Can be repeated.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Write report to file path instead of stdout.",
    )
    parser.add_argument(
        "--fail-on-conflict",
        action="store_true",
        help="Exit with code 1 if any explicit, component-induced, or effective conflict is found.",
    )
    parser.add_argument(
        "--transitive-mode",
        choices=["auto", "off", "required"],
        default="auto",
        help="How to run Maven transitive dependency analysis.",
    )
    parser.add_argument(
        "--mvn-bin",
        default="",
        help="Override the Maven executable used for transitive analysis.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_dir = Path(args.root).resolve()
    if not root_dir.exists():
        print(f"[ERROR] Root directory does not exist: {root_dir}", file=sys.stderr)
        return 2

    min_occurrences = max(2, args.min_occurrences)
    ignored_dirs = [".git", "target", ".idea", ".mvn", ".gradle", "node_modules"]
    ignored_dirs.extend(args.ignore_dir)

    pom_files = find_pom_files(root_dir, ignored_dirs)
    if not pom_files:
        print(f"[WARN] No pom.xml found under {root_dir}", file=sys.stderr)
        return 0

    pom_results: List[PomParseResult] = [parse_pom(pom, root_dir) for pom in pom_files]
    entries: List[VersionEntry] = []
    module_to_pom: Dict[str, str] = {}

    for result in pom_results:
        entries.extend(result.entries)
        module_to_pom.setdefault(result.module, result.rel_pom)

    component_entries = build_component_propagation_entries(pom_results)
    transitive_scan = run_transitive_scan(
        root_dir, args.transitive_mode, args.mvn_bin, module_to_pom
    )

    if args.transitive_mode == "required" and not transitive_scan.succeeded:
        print(
            f"[ERROR] Required transitive scan failed: {transitive_scan.error}",
            file=sys.stderr,
        )
        return 2

    if args.transitive_mode == "auto" and transitive_scan.error:
        print(
            f"[WARN] Transitive dependency scan unavailable: {transitive_scan.error}",
            file=sys.stderr,
        )

    payload = build_report_payload(
        root_dir,
        pom_files,
        entries,
        component_entries,
        min_occurrences,
        transitive_scan,
    )

    if args.format == "json":
        rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        rendered = render_markdown(payload, min_occurrences)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"[INFO] Report written to {output_path}")
    else:
        print(rendered)

    summary = payload["summary"]
    has_conflict = any(
        (
            summary["dependency_conflicts"] > 0,
            summary["plugin_conflicts"] > 0,
            summary["property_conflicts"] > 0,
            summary["component_indirect_conflicts"] > 0,
            summary["effective_dependency_conflicts"] > 0,
            summary["indirect_dependency_conflicts"] > 0,
            summary["transitive_conflict_hints"] > 0,
        )
    )
    if args.fail_on_conflict and has_conflict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
