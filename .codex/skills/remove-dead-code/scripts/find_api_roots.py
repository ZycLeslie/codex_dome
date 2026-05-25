#!/usr/bin/env python3
"""Scan YAML/JSON interface files for API roots and source references.

This helper is intentionally heuristic and dependency-free. It surfaces
OpenAPI/Swagger-style roots so an agent can protect them before dead-code
deletion; it is not a complete YAML parser.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional


HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}
DEFAULT_EXCLUDES = {
    ".git",
    ".codex",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
    "target",
}
SPEC_SUFFIXES = {".yaml", ".yml", ".json"}
SOURCE_SUFFIXES = {
    ".java",
    ".kt",
    ".scala",
    ".groovy",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".go",
    ".cs",
    ".rb",
    ".php",
    ".xml",
    ".properties",
}


@dataclass
class ApiRoot:
    spec_file: str
    line: int
    method: str
    path: str
    operation_id: Optional[str]
    handlers: list[str]
    source_refs: list[str]


def iter_files(root: Path, suffixes: set[str], excludes: set[str], max_bytes: int) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() not in suffixes:
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            yield path


def clean_yaml_value(value: str) -> str:
    value = value.strip().split("#", 1)[0].strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    return value


def yaml_roots(path: Path, repo: Path) -> list[ApiRoot]:
    roots: list[ApiRoot] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return roots

    current_path: Optional[str] = None
    current_path_line = 0
    current_path_indent = -1
    current_method: Optional[str] = None
    current_method_line = 0
    current_operation: Optional[str] = None
    current_handlers: list[str] = []

    def flush() -> None:
        nonlocal current_method, current_operation, current_handlers, current_method_line
        if current_path and current_method:
            roots.append(
                ApiRoot(
                    spec_file=rel(path, repo),
                    line=current_method_line or current_path_line,
                    method=current_method.upper(),
                    path=current_path,
                    operation_id=current_operation,
                    handlers=sorted(set(current_handlers)),
                    source_refs=[],
                )
            )
        current_method = None
        current_operation = None
        current_handlers = []
        current_method_line = 0

    for number, raw in enumerate(lines, start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()

        path_match = re.match(r"""^['"]?(/[^:'"]*)['"]?\s*:""", stripped)
        if path_match:
            flush()
            current_path = clean_yaml_value(path_match.group(1))
            current_path_line = number
            current_path_indent = indent
            continue

        if current_path and indent <= current_path_indent and re.match(r"^[A-Za-z0-9_.-]+\s*:", stripped):
            flush()
            current_path = None
            current_path_indent = -1

        key_match = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", stripped)
        if not current_path or not key_match:
            continue

        key = key_match.group(1)
        value = clean_yaml_value(key_match.group(2))
        lower_key = key.lower()

        if lower_key in HTTP_METHODS:
            flush()
            current_method = lower_key
            current_method_line = number
            continue

        if not current_method:
            continue

        if key == "operationId" and value:
            current_operation = value
        elif lower_key in {"x-handler", "x-controller", "x-service", "handler", "controller", "service", "method", "interface", "class"} and value:
            current_handlers.append(value)

    flush()
    return roots


def json_roots(path: Path, repo: Path) -> list[ApiRoot]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError):
        return []

    roots: list[ApiRoot] = []
    paths = data.get("paths") if isinstance(data, dict) else None
    if not isinstance(paths, dict):
        return roots

    for api_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            handlers = []
            for key in ("x-handler", "x-controller", "x-service", "handler", "controller", "service", "method", "interface", "class"):
                value = operation.get(key)
                if isinstance(value, str):
                    handlers.append(value)
            roots.append(
                ApiRoot(
                    spec_file=rel(path, repo),
                    line=1,
                    method=method.upper(),
                    path=str(api_path),
                    operation_id=operation.get("operationId") if isinstance(operation.get("operationId"), str) else None,
                    handlers=sorted(set(handlers)),
                    source_refs=[],
                )
            )
    return roots


def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def source_index(repo: Path, excludes: set[str], max_bytes: int) -> list[tuple[Path, list[str]]]:
    indexed: list[tuple[Path, list[str]]] = []
    for path in iter_files(repo, SOURCE_SUFFIXES, excludes, max_bytes):
        try:
            indexed.append((path, path.read_text(encoding="utf-8", errors="ignore").splitlines()))
        except OSError:
            continue
    return indexed


def operation_variants(name: str) -> set[str]:
    variants = {name}
    words = re.split(r"[-_.\s]+", name)
    if len(words) > 1:
        variants.add(words[0] + "".join(w[:1].upper() + w[1:] for w in words[1:] if w))
        variants.add("_".join(w.lower() for w in words if w))
        variants.add("-".join(w.lower() for w in words if w))
    return {v for v in variants if v}


def add_source_refs(roots: list[ApiRoot], indexed_sources: list[tuple[Path, list[str]]], repo: Path) -> None:
    for root in roots:
        needles = set(root.handlers)
        if root.operation_id:
            needles.update(operation_variants(root.operation_id))
        if root.path:
            needles.add(root.path)
            normalized = re.sub(r"\{[^}]+\}", "", root.path).rstrip("/")
            if normalized and normalized != root.path:
                needles.add(normalized)

        refs: list[str] = []
        for source_path, lines in indexed_sources:
            for line_no, line in enumerate(lines, start=1):
                for needle in needles:
                    if not needle:
                        continue
                    if needle in line:
                        refs.append(f"{rel(source_path, repo)}:{line_no}:{needle}")
                        break
                if len(refs) >= 20:
                    break
            if len(refs) >= 20:
                break
        root.source_refs = refs


def write_markdown(roots: list[ApiRoot], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# API Roots",
        "",
        "| Spec | Line | Method | Path | Operation | Handlers | Source refs |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for root in roots:
        refs = "<br>".join(root.source_refs[:5])
        handlers = "<br>".join(root.handlers)
        lines.append(
            f"| {root.spec_file} | {root.line} | {root.method} | `{root.path}` | "
            f"{root.operation_id or ''} | {handlers} | {refs} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root")
    parser.add_argument("--output", default=".codex/dead-code/api-roots.json", help="JSON output path")
    parser.add_argument("--markdown", help="Optional Markdown output path")
    parser.add_argument("--exclude-dir", action="append", default=[], help="Directory name to exclude")
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    excludes = DEFAULT_EXCLUDES | set(args.exclude_dir)

    roots: list[ApiRoot] = []
    for spec_file in iter_files(repo, SPEC_SUFFIXES, excludes, args.max_file_bytes):
        if spec_file.suffix.lower() == ".json":
            parsed = json_roots(spec_file, repo)
            roots.extend(parsed if parsed else yaml_roots(spec_file, repo))
        else:
            roots.extend(yaml_roots(spec_file, repo))

    add_source_refs(roots, source_index(repo, excludes, args.max_file_bytes), repo)
    roots.sort(key=lambda r: (r.spec_file, r.line, r.method, r.path))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(root) for root in roots], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.markdown:
        write_markdown(roots, Path(args.markdown))

    print(f"Found {len(roots)} API roots")
    print(f"Wrote {output}")
    if args.markdown:
        print(f"Wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
