#!/usr/bin/env python3
"""Generate a categorized method inventory for a source repository."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript React",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".h": "C/C++ Header",
    ".hh": "C++ Header",
    ".hpp": "C++ Header",
    ".rs": "Rust",
    ".swift": "Swift",
}

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".codex",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "bower_components",
    "dist",
    "build",
    "coverage",
    "target",
    "out",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    ".cache",
    "vendor",
    "Pods",
    "DerivedData",
}

DEFAULT_EXCLUDE_GLOBS = {
    "*.min.js",
    "*.bundle.js",
    "*.map",
    "*.d.ts",
    "*.generated.*",
    "*_generated.*",
    "generated_*",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}

CATEGORY_RULES = [
    (
        "Tests",
        {
            "test",
            "tests",
            "spec",
            "specs",
            "fixture",
            "fixtures",
            "mock",
            "mocks",
            "stub",
            "assert",
            "describe",
        },
    ),
    (
        "API, Routing, and Controllers",
        {
            "api",
            "route",
            "router",
            "controller",
            "endpoint",
            "handler",
            "middleware",
            "request",
            "response",
            "resolver",
            "graphql",
            "rpc",
            "servlet",
            "action",
            "view",
        },
    ),
    (
        "Auth and Security",
        {
            "auth",
            "authenticate",
            "authorization",
            "authorize",
            "login",
            "logout",
            "token",
            "jwt",
            "oauth",
            "permission",
            "role",
            "acl",
            "csrf",
            "encrypt",
            "decrypt",
            "hash",
            "password",
            "session",
            "secret",
        },
    ),
    (
        "Validation, Parsing, and Mapping",
        {
            "validate",
            "validation",
            "schema",
            "parse",
            "parser",
            "serialize",
            "deserialize",
            "normalize",
            "sanitize",
            "transform",
            "map",
            "mapper",
            "convert",
            "format",
            "decode",
            "encode",
        },
    ),
    (
        "Data Access and Persistence",
        {
            "repository",
            "repo",
            "dao",
            "model",
            "entity",
            "migration",
            "query",
            "sql",
            "db",
            "database",
            "collection",
            "store",
            "cache",
            "index",
            "find",
            "load",
            "save",
            "insert",
            "select",
            "delete",
            "persist",
            "transaction",
        },
    ),
    (
        "Business Services and Workflows",
        {
            "service",
            "manager",
            "coordinator",
            "workflow",
            "usecase",
            "policy",
            "calculate",
            "compute",
            "process",
            "execute",
            "apply",
            "approve",
            "reject",
            "schedule",
            "orchestrate",
            "resolve",
        },
    ),
    (
        "UI and Presentation",
        {
            "ui",
            "component",
            "render",
            "view",
            "page",
            "screen",
            "modal",
            "dialog",
            "form",
            "button",
            "layout",
            "style",
            "tooltip",
            "canvas",
            "widget",
        },
    ),
    (
        "Integrations, Jobs, and I/O",
        {
            "client",
            "adapter",
            "gateway",
            "sdk",
            "email",
            "sms",
            "webhook",
            "queue",
            "worker",
            "job",
            "cron",
            "stream",
            "file",
            "upload",
            "download",
            "socket",
            "external",
            "sync",
            "fetch",
            "http",
        },
    ),
    (
        "Error Handling and Logging",
        {
            "error",
            "exception",
            "log",
            "logger",
            "warn",
            "warning",
            "retry",
            "fallback",
            "recover",
            "fail",
            "failure",
        },
    ),
    (
        "Configuration and Bootstrapping",
        {
            "config",
            "configure",
            "setup",
            "init",
            "initialize",
            "bootstrap",
            "main",
            "cli",
            "command",
            "start",
            "stop",
            "register",
            "factory",
            "provider",
            "module",
            "plugin",
        },
    ),
    (
        "Utilities and Shared Helpers",
        {
            "util",
            "utils",
            "utility",
            "helper",
            "helpers",
            "common",
            "shared",
            "lib",
            "support",
            "tool",
            "tools",
        },
    ),
]

CATEGORY_ORDER = [name for name, _ in CATEGORY_RULES] + ["Uncategorized"]

CONTROL_WORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "with",
    "return",
    "throw",
    "else",
    "do",
    "try",
    "finally",
    "class",
    "new",
    "function",
    "import",
    "export",
}


@dataclass
class MethodRecord:
    name: str
    qualified_name: str
    owner: str
    kind: str
    file: str
    line: int
    language: str
    signature: str
    category: str = "Uncategorized"
    flags: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate categorized Markdown and JSON inventories of repository methods."
    )
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--output",
        default=None,
        help="Markdown output path. Defaults to <repo>/.codex/method-index/methods.md.",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="JSON output path. Defaults to the Markdown output path with .json suffix.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories and files that are skipped by default.",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude. May be passed multiple times.",
    )
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="File glob to exclude. May be passed multiple times.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=2_000_000,
        help="Skip source files larger than this many bytes. Default: 2000000.",
    )
    return parser.parse_args()


def normalize_path(path: Path) -> str:
    return path.as_posix()


def text_signature(lines: list[str], start_line: int, max_lines: int = 4) -> str:
    collected: list[str] = []
    parens = 0
    for index in range(start_line - 1, min(len(lines), start_line - 1 + max_lines)):
        piece = lines[index].strip()
        if not piece:
            continue
        collected.append(piece)
        parens += piece.count("(") - piece.count(")")
        if parens <= 0 and (
            piece.endswith(":")
            or piece.endswith("{")
            or piece.endswith("=>")
            or "{" in piece
            or "=>" in piece
        ):
            break
    return compact(" ".join(collected))


def compact(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def strip_line_comment(line: str, language: str) -> str:
    if language in {"Python", "Ruby"}:
        return line.split("#", 1)[0]
    return line.split("//", 1)[0]


def classify(record: MethodRecord) -> str:
    path_text = record.file.lower().replace("\\", "/")
    name_text = split_identifier(record.name)
    owner_text = split_identifier(record.owner)
    signature_text = split_identifier(record.signature)
    combined = f"{path_text} {name_text} {owner_text} {signature_text}"

    name_lower = record.name.lower()
    if is_test_path(path_text) or name_lower.startswith("test") or name_lower.startswith("should"):
        return "Tests"

    best_category = "Uncategorized"
    best_score = 0
    for category, keywords in CATEGORY_RULES:
        if category == "Tests":
            continue
        score = 0
        for keyword in keywords:
            if keyword in path_text:
                score += 3
            if keyword in name_text:
                score += 4
            if keyword in owner_text:
                score += 2
            if keyword in signature_text:
                score += 1
            if re.search(rf"(^|[^a-z0-9]){re.escape(keyword)}([^a-z0-9]|$)", combined):
                score += 1
        if score > best_score:
            best_category = category
            best_score = score
    return best_category


def split_identifier(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return value.lower()


def is_test_path(path_text: str) -> bool:
    parts = set(path_text.split("/"))
    name = path_text.rsplit("/", 1)[-1]
    return (
        "test" in parts
        or "tests" in parts
        or "__tests__" in parts
        or "spec" in parts
        or "specs" in parts
        or ".test." in name
        or ".spec." in name
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def iter_source_files(
    root: Path,
    include_hidden: bool,
    exclude_dirs: set[str],
    exclude_globs: set[str],
    max_file_bytes: int,
) -> tuple[list[Path], list[dict[str, str]]]:
    source_files: list[Path] = []
    skipped: list[dict[str, str]] = []

    for current_dir, dir_names, file_names in os.walk(root):
        current = Path(current_dir)
        kept_dirs = []
        for dirname in dir_names:
            child = current / dirname
            reason = skip_dir_reason(child, root, include_hidden, exclude_dirs)
            if reason:
                skipped.append({"path": normalize_path(child.relative_to(root)), "reason": reason})
            else:
                kept_dirs.append(dirname)
        dir_names[:] = kept_dirs

        for filename in file_names:
            path = current / filename
            reason = skip_file_reason(
                path, root, include_hidden, exclude_globs, max_file_bytes
            )
            if reason:
                if path.suffix in LANGUAGES:
                    skipped.append(
                        {"path": normalize_path(path.relative_to(root)), "reason": reason}
                    )
                continue
            source_files.append(path)

    return source_files, skipped


def skip_dir_reason(
    path: Path, root: Path, include_hidden: bool, exclude_dirs: set[str]
) -> str | None:
    name = path.name
    if name in exclude_dirs:
        return "excluded directory"
    if not include_hidden and name.startswith("."):
        return "hidden directory"
    return None


def skip_file_reason(
    path: Path,
    root: Path,
    include_hidden: bool,
    exclude_globs: set[str],
    max_file_bytes: int,
) -> str | None:
    if path.suffix not in LANGUAGES:
        return "unsupported extension"
    rel = normalize_path(path.relative_to(root))
    if not include_hidden and any(part.startswith(".") for part in path.relative_to(root).parts):
        return "hidden file"
    if any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in exclude_globs):
        return "excluded glob"
    try:
        size = path.stat().st_size
    except OSError as exc:
        return f"stat failed: {exc}"
    if size > max_file_bytes:
        return f"larger than {max_file_bytes} bytes"
    return None


def parse_file(path: Path, root: Path) -> tuple[list[MethodRecord], str | None]:
    language = LANGUAGES[path.suffix]
    rel = normalize_path(path.relative_to(root))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], f"read failed: {exc}"

    lines = text.splitlines()
    if language == "Python":
        records = parse_python(text, lines, rel, language)
    elif language.startswith("JavaScript") or language.startswith("TypeScript"):
        records = parse_javascript_like(lines, rel, language)
    elif language == "Go":
        records = parse_go(lines, rel, language)
    elif language == "Ruby":
        records = parse_ruby(lines, rel, language)
    elif language == "Rust":
        records = parse_rust(lines, rel, language)
    elif language == "Swift":
        records = parse_swift(lines, rel, language)
    elif language == "Kotlin":
        records = parse_kotlin(lines, rel, language)
    elif language == "PHP":
        records = parse_php(lines, rel, language)
    else:
        records = parse_c_family(lines, rel, language)

    for record in records:
        record.category = classify(record)
    return dedupe(records), None


def parse_python(
    text: str, lines: list[str], rel: str, language: str
) -> list[MethodRecord]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return parse_python_regex(lines, rel, language)

    records: list[MethodRecord] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.add_function(node, "method" if self.stack else "function", ())

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.add_function(node, "method" if self.stack else "function", ("async",))

        def add_function(
            self,
            node: ast.FunctionDef | ast.AsyncFunctionDef,
            kind: str,
            flags: tuple[str, ...],
        ) -> None:
            owner = ".".join(self.stack)
            qualified = f"{owner}.{node.name}" if owner else node.name
            records.append(
                MethodRecord(
                    name=node.name,
                    qualified_name=qualified,
                    owner=owner,
                    kind=kind,
                    file=rel,
                    line=node.lineno,
                    language=language,
                    signature=text_signature(lines, node.lineno),
                    flags=flags,
                )
            )
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

    Visitor().visit(tree)
    return records


def parse_python_regex(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(r"^\s*(async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    for index, line in enumerate(lines, start=1):
        match = pattern.match(line)
        if not match:
            continue
        records.append(
            MethodRecord(
                name=match.group(2),
                qualified_name=match.group(2),
                owner="",
                kind="function",
                file=rel,
                line=index,
                language=language,
                signature=text_signature(lines, index),
                flags=("async",) if match.group(1) else (),
            )
        )
    return records


def parse_javascript_like(
    lines: list[str], rel: str, language: str
) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    class_stack: list[tuple[str, int]] = []
    brace_depth = 0
    pending_class: str | None = None

    function_decl = re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?(async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)?\s*\("
    )
    arrow_decl = re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
    )
    function_expr = re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)?\s*\("
    )
    property_func = re.compile(
        r"^\s*([A-Za-z_$][\w$]*)\s*:\s*(async\s+)?(?:function\s*\*?\s*)?\("
    )
    property_arrow = re.compile(
        r"^\s*([A-Za-z_$][\w$]*)\s*:\s*(async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
    )
    method_decl = re.compile(
        r"^\s*(?:(?:public|private|protected|static|async|get|set|override|readonly)\s+)*([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*(?::\s*[^={]+)?\s*\{?\s*$"
    )
    class_decl = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")

    for index, raw_line in enumerate(lines, start=1):
        line = strip_line_comment(raw_line, language).strip()
        if not line:
            continue

        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()

        class_match = class_decl.search(line)
        if class_match:
            pending_class = class_match.group(1)

        owner = class_stack[-1][0] if class_stack else ""
        record = None

        match = function_decl.match(line)
        if match:
            name = match.group(2) or "default"
            record = make_record(name, "", "function", rel, index, language, lines, ("async",) if match.group(1) else ())
        else:
            match = function_expr.match(line)
            if match:
                flags = ("async",) if match.group(2) else ()
                record = make_record(match.group(1), "", "function", rel, index, language, lines, flags)

        if record is None:
            match = arrow_decl.match(line)
            if match:
                flags = ("async",) if match.group(2) else ()
                record = make_record(match.group(1), "", "function", rel, index, language, lines, flags)

        if record is None:
            for pattern in (property_func, property_arrow):
                match = pattern.match(line)
                if match and match.group(1) not in CONTROL_WORDS:
                    flags = ("async",) if match.group(2) else ()
                    record = make_record(match.group(1), owner, "property function", rel, index, language, lines, flags)
                    break

        if record is None:
            match = method_decl.match(line)
            if match:
                name = match.group(1)
                if name not in CONTROL_WORDS and not line.startswith(("return ", "throw ")):
                    flags = ("async",) if re.search(r"\basync\b", line) else ()
                    record = make_record(name, owner, "method", rel, index, language, lines, flags)

        if record:
            records.append(record)

        opens = line.count("{")
        closes = line.count("}")
        new_depth = brace_depth + opens - closes
        if pending_class and opens:
            class_stack.append((pending_class, brace_depth + 1))
            pending_class = None
        brace_depth = max(new_depth, 0)

    return records


def make_record(
    name: str,
    owner: str,
    kind: str,
    rel: str,
    line: int,
    language: str,
    lines: list[str],
    flags: tuple[str, ...] = (),
) -> MethodRecord:
    qualified = f"{owner}.{name}" if owner else name
    return MethodRecord(
        name=name,
        qualified_name=qualified,
        owner=owner,
        kind=kind,
        file=rel,
        line=line,
        language=language,
        signature=text_signature(lines, line),
        flags=flags,
    )


def parse_go(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(
        r"^\s*func\s+(?:\((?P<receiver>[^)]*)\)\s*)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
    )
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        owner = compact(match.group("receiver") or "", 80)
        records.append(make_record(match.group("name"), owner, "method" if owner else "function", rel, index, language, lines))
    return records


def parse_ruby(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(r"^\s*def\s+(?:(self)\.)?([A-Za-z_][A-Za-z0-9_]*[!?=]?)")
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        owner = "self" if match.group(1) else ""
        records.append(make_record(match.group(2), owner, "method", rel, index, language, lines))
    return records


def parse_rust(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(
        r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\("
    )
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        flags = tuple(flag for flag in ("async", "unsafe") if re.search(rf"\b{flag}\b", line))
        records.append(make_record(match.group(1), "", "function", rel, index, language, lines, flags))
    return records


def parse_swift(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(r"^\s*(?:public|private|internal|fileprivate|open|static|class|mutating|override|\s)*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        records.append(make_record(match.group(1), "", "function", rel, index, language, lines))
    return records


def parse_kotlin(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(
        r"^\s*(?:public|private|protected|internal|override|suspend|inline|tailrec|operator|open|final|abstract|\s)*fun\s+(?:[A-Za-z_][A-Za-z0-9_]*\.)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\("
    )
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        flags = ("suspend",) if re.search(r"\bsuspend\b", line) else ()
        records.append(make_record(match.group(1), "", "function", rel, index, language, lines, flags))
    return records


def parse_php(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    pattern = re.compile(
        r"^\s*(?:public|private|protected|static|final|abstract|\s)*function\s+&?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\("
    )
    for index, line in enumerate(lines, start=1):
        match = pattern.match(strip_line_comment(line, language))
        if not match:
            continue
        records.append(make_record(match.group(1), "", "function", rel, index, language, lines))
    return records


def parse_c_family(lines: list[str], rel: str, language: str) -> list[MethodRecord]:
    records: list[MethodRecord] = []
    method_pattern = re.compile(
        r"^\s*(?:(?:public|private|protected|internal|static|final|abstract|virtual|override|async|sealed|extern|inline|constexpr|synchronized|native)\s+)*"
        r"(?:[A-Za-z_][\w:<>,~\[\]\s*&?.]+\s+)?"
        r"([A-Za-z_~][A-Za-z0-9_~]*)\s*\([^;]*\)\s*(?:const\s*)?(?:throws\s+[^{]+)?\s*\{?\s*$"
    )
    annotation = re.compile(r"^\s*@")
    for index, raw_line in enumerate(lines, start=1):
        line = strip_line_comment(raw_line, language).strip()
        if not line or annotation.match(line):
            continue
        match = method_pattern.match(line)
        if not match:
            continue
        name = match.group(1)
        if name in CONTROL_WORDS:
            continue
        flags = tuple(flag for flag in ("static", "async") if re.search(rf"\b{flag}\b", line))
        records.append(make_record(name, "", "method", rel, index, language, lines, flags))
    return records


def dedupe(records: list[MethodRecord]) -> list[MethodRecord]:
    seen: set[tuple[str, int, str, str]] = set()
    unique: list[MethodRecord] = []
    for record in records:
        key = (record.file, record.line, record.name, record.kind)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def summarize_files(methods: list[MethodRecord]) -> list[dict[str, object]]:
    grouped: dict[str, list[MethodRecord]] = defaultdict(list)
    for method in methods:
        grouped[method.file].append(method)

    rows: list[dict[str, object]] = []
    for file, items in grouped.items():
        category_counts = Counter(item.category for item in items)
        language_counts = Counter(item.language for item in items)
        rows.append(
            {
                "file": file,
                "methods": len(items),
                "language": language_counts.most_common(1)[0][0],
                "categories": dict(category_counts.most_common()),
            }
        )
    rows.sort(key=lambda item: (-int(item["methods"]), str(item["file"])))
    return rows


def repeated_names(methods: list[MethodRecord]) -> list[dict[str, object]]:
    by_name: dict[str, list[MethodRecord]] = defaultdict(list)
    for method in methods:
        by_name[method.name.lower()].append(method)

    repeats: list[dict[str, object]] = []
    for name, items in by_name.items():
        files = sorted({item.file for item in items})
        if len(files) < 2:
            continue
        repeats.append(
            {
                "name": name,
                "count": len(items),
                "files": files,
                "categories": dict(Counter(item.category for item in items).most_common()),
            }
        )
    repeats.sort(key=lambda item: (-int(item["count"]), str(item["name"])))
    return repeats


def render_markdown(
    root: Path,
    methods: list[MethodRecord],
    skipped: list[dict[str, str]],
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    category_counts = Counter(method.category for method in methods)
    language_counts = Counter(method.language for method in methods)
    file_rows = summarize_files(methods)
    repeats = repeated_names(methods)

    lines: list[str] = []
    lines.append("# Repository Method Inventory")
    lines.append("")
    lines.append(f"- Repository: `{root}`")
    lines.append(f"- Generated: `{generated_at}`")
    lines.append(f"- Methods indexed: `{len(methods)}`")
    lines.append(f"- Files with methods: `{len(file_rows)}`")
    lines.append("")
    lines.append("## How To Use")
    lines.append("")
    lines.append("- Search this file before adding new logic.")
    lines.append("- Start with feature nouns, model names, endpoint names, and operation verbs.")
    lines.append("- Open the source file and line before reusing or changing behavior.")
    lines.append("- Review repeated method names for possible duplicate logic or framework hooks.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("### Categories")
    lines.append("")
    lines.append("| Category | Methods | Files |")
    lines.append("| --- | ---: | ---: |")
    for category in CATEGORY_ORDER:
        count = category_counts.get(category, 0)
        if not count:
            continue
        file_count = len({method.file for method in methods if method.category == category})
        lines.append(f"| {category} | {count} | {file_count} |")
    lines.append("")

    lines.append("### Languages")
    lines.append("")
    lines.append("| Language | Methods |")
    lines.append("| --- | ---: |")
    for language, count in language_counts.most_common():
        lines.append(f"| {language} | {count} |")
    lines.append("")

    lines.append("## File Checklist")
    lines.append("")
    lines.append("| File | Methods | Main Categories |")
    lines.append("| --- | ---: | --- |")
    for row in file_rows:
        categories = ", ".join(
            f"{name} ({count})" for name, count in list(row["categories"].items())[:3]
        )
        lines.append(f"| `{row['file']}` | {row['methods']} | {categories} |")
    lines.append("")

    lines.append("## Methods By Category")
    lines.append("")
    by_category: dict[str, list[MethodRecord]] = defaultdict(list)
    for method in methods:
        by_category[method.category].append(method)

    for category in CATEGORY_ORDER:
        items = sorted(by_category.get(category, []), key=lambda item: (item.file, item.line))
        if not items:
            continue
        lines.append(f"### {category} ({len(items)})")
        lines.append("")
        by_file: dict[str, list[MethodRecord]] = defaultdict(list)
        for item in items:
            by_file[item.file].append(item)
        for file in sorted(by_file):
            lines.append(f"#### `{file}`")
            for item in sorted(by_file[file], key=lambda record: record.line):
                flags = f" [{', '.join(item.flags)}]" if item.flags else ""
                owner = f" owner `{item.owner}`" if item.owner else ""
                lines.append(
                    f"- line {item.line}: `{item.qualified_name}` ({item.kind}, {item.language}{flags}){owner} - `{item.signature}`"
                )
            lines.append("")

    lines.append("## Repeated Method Names")
    lines.append("")
    if repeats:
        lines.append("| Name | Count | Categories | Files |")
        lines.append("| --- | ---: | --- | --- |")
        for item in repeats[:100]:
            categories = ", ".join(f"{name} ({count})" for name, count in item["categories"].items())
            files = "<br>".join(f"`{file}`" for file in item["files"][:8])
            if len(item["files"]) > 8:
                files += f"<br>... +{len(item['files']) - 8} more"
            lines.append(f"| `{item['name']}` | {item['count']} | {categories} | {files} |")
    else:
        lines.append("No method names were repeated across multiple files.")
    lines.append("")

    lines.append("## Skipped Inputs")
    lines.append("")
    source_skips = [item for item in skipped if item["reason"] != "unsupported extension"]
    if source_skips:
        lines.append("| Path | Reason |")
        lines.append("| --- | --- |")
        for item in source_skips[:200]:
            lines.append(f"| `{item['path']}` | {item['reason']} |")
        if len(source_skips) > 200:
            lines.append(f"| ... | {len(source_skips) - 200} more skipped inputs omitted |")
    else:
        lines.append("No supported source files were skipped.")
    lines.append("")
    return "\n".join(lines)


def build_json(
    root: Path, methods: list[MethodRecord], skipped: list[dict[str, str]]
) -> dict[str, object]:
    category_counts = Counter(method.category for method in methods)
    language_counts = Counter(method.language for method in methods)
    return {
        "metadata": {
            "repository": str(root),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "method_count": len(methods),
            "file_count": len({method.file for method in methods}),
        },
        "categories": dict(category_counts.most_common()),
        "languages": dict(language_counts.most_common()),
        "files": summarize_files(methods),
        "repeated_method_names": repeated_names(methods),
        "methods": [asdict(method) for method in methods],
        "skipped_inputs": skipped,
    }


def main() -> int:
    args = parse_args()
    root = Path(args.repo).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: repository path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    output = (
        Path(args.output).expanduser()
        if args.output
        else root / ".codex" / "method-index" / "methods.md"
    )
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    json_output = (
        Path(args.json_output).expanduser()
        if args.json_output
        else output.with_suffix(".json")
    )
    if not json_output.is_absolute():
        json_output = (Path.cwd() / json_output).resolve()

    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS) | set(args.exclude_dir)
    exclude_globs = set(DEFAULT_EXCLUDE_GLOBS) | set(args.exclude_glob)
    source_files, skipped = iter_source_files(
        root,
        include_hidden=args.include_hidden,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        max_file_bytes=args.max_file_bytes,
    )

    methods: list[MethodRecord] = []
    for path in source_files:
        records, error = parse_file(path, root)
        if error:
            skipped.append({"path": normalize_path(path.relative_to(root)), "reason": error})
            continue
        methods.extend(records)

    methods.sort(key=lambda record: (record.category, record.file, record.line, record.name))

    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(root, methods, skipped), encoding="utf-8")
    json_output.write_text(json.dumps(build_json(root, methods, skipped), indent=2), encoding="utf-8")

    print(f"Indexed {len(methods)} methods from {len(source_files)} source files.")
    print(f"Markdown: {output}")
    print(f"JSON: {json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
