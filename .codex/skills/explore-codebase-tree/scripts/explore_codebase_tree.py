#!/usr/bin/env python3
"""Generate a categorized, tree-style callable map for a source repository."""

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
    ".vue": "Vue",
    ".svelte": "Svelte",
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

CONTROL_WORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "else",
    "do",
    "try",
    "return",
    "throw",
    "new",
    "await",
    "with",
    "using",
    "lock",
}

CATEGORY_ORDER = [
    "Tests and Quality",
    "API, Routing, and Controllers",
    "Auth and Security",
    "Validation, Parsing, and Mapping",
    "Data Access and Persistence",
    "Business Services and Workflows",
    "UI and Presentation",
    "Integrations, Jobs, and I/O",
    "Error Handling and Observability",
    "Configuration and Bootstrapping",
    "Build, Tooling, and Scripts",
    "Utilities and Shared Helpers",
    "Uncategorized Domain Logic",
]

CATEGORY_RULES = [
    (
        "Tests and Quality",
        {
            "test",
            "tests",
            "fixture",
            "fixtures",
            "mock",
            "mocks",
            "stub",
            "stubs",
            "assert",
            "describe",
            "expect",
            "verify",
            "quality",
        },
    ),
    (
        "API, Routing, and Controllers",
        {
            "api",
            "route",
            "routes",
            "router",
            "controller",
            "controllers",
            "endpoint",
            "handler",
            "handlers",
            "middleware",
            "request",
            "response",
            "resolver",
            "graphql",
            "rpc",
            "servlet",
            "action",
            "view",
            "post",
            "put",
            "patch",
        },
    ),
    (
        "Auth and Security",
        {
            "auth",
            "authenticate",
            "authenticated",
            "authentication",
            "authorize",
            "authorization",
            "login",
            "logout",
            "token",
            "jwt",
            "oauth",
            "permission",
            "permissions",
            "role",
            "roles",
            "acl",
            "csrf",
            "encrypt",
            "decrypt",
            "hash",
            "password",
            "session",
            "secret",
            "secure",
            "security",
        },
    ),
    (
        "Validation, Parsing, and Mapping",
        {
            "validate",
            "validator",
            "validation",
            "schema",
            "parse",
            "parser",
            "serialize",
            "deserialize",
            "normalize",
            "sanitise",
            "sanitize",
            "transform",
            "map",
            "mapper",
            "convert",
            "format",
            "decode",
            "encode",
            "marshal",
            "unmarshal",
            "bind",
        },
    ),
    (
        "Data Access and Persistence",
        {
            "repository",
            "repositories",
            "repo",
            "dao",
            "model",
            "models",
            "entity",
            "entities",
            "migration",
            "query",
            "sql",
            "db",
            "database",
            "collection",
            "store",
            "storage",
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
            "record",
        },
    ),
    (
        "Business Services and Workflows",
        {
            "service",
            "services",
            "manager",
            "coordinator",
            "workflow",
            "usecase",
            "usecases",
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
            "create",
            "update",
            "cancel",
            "submit",
            "complete",
            "sync",
        },
    ),
    (
        "UI and Presentation",
        {
            "ui",
            "view",
            "views",
            "page",
            "pages",
            "component",
            "components",
            "screen",
            "render",
            "renderer",
            "template",
            "layout",
            "style",
            "css",
            "html",
            "dom",
            "click",
            "input",
            "form",
            "modal",
            "popup",
            "display",
            "paint",
        },
    ),
    (
        "Integrations, Jobs, and I/O",
        {
            "client",
            "adapter",
            "integration",
            "integrations",
            "webhook",
            "webhooks",
            "job",
            "jobs",
            "worker",
            "queue",
            "task",
            "cron",
            "scheduler",
            "poll",
            "fetch",
            "send",
            "receive",
            "upload",
            "download",
            "import",
            "export",
            "file",
            "files",
            "stream",
            "socket",
            "email",
            "http",
            "io",
        },
    ),
    (
        "Error Handling and Observability",
        {
            "error",
            "errors",
            "exception",
            "exceptions",
            "fail",
            "failure",
            "retry",
            "recover",
            "fallback",
            "log",
            "logger",
            "logging",
            "trace",
            "metric",
            "metrics",
            "monitor",
            "observe",
            "instrument",
            "warn",
            "debug",
        },
    ),
    (
        "Configuration and Bootstrapping",
        {
            "config",
            "configuration",
            "settings",
            "option",
            "options",
            "env",
            "environment",
            "bootstrap",
            "startup",
            "init",
            "initialize",
            "main",
            "setup",
            "install",
            "load",
            "register",
            "factory",
            "provider",
        },
    ),
    (
        "Build, Tooling, and Scripts",
        {
            "build",
            "tool",
            "tools",
            "script",
            "scripts",
            "cli",
            "command",
            "generator",
            "generate",
            "scaffold",
            "lint",
            "format",
            "compile",
            "bundle",
            "deploy",
            "release",
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
            "base",
            "core",
            "lib",
            "libs",
            "string",
            "array",
            "date",
            "time",
            "number",
            "math",
            "merge",
            "clone",
            "copy",
            "sort",
            "filter",
        },
    ),
]

CATEGORY_PURPOSES = {
    "Tests and Quality": "test or quality-assurance behavior",
    "API, Routing, and Controllers": "request routing or controller behavior",
    "Auth and Security": "authentication, authorization, or security behavior",
    "Validation, Parsing, and Mapping": "validation, parsing, formatting, or data mapping",
    "Data Access and Persistence": "data access, persistence, querying, or storage behavior",
    "Business Services and Workflows": "business workflow or service orchestration",
    "UI and Presentation": "user-interface or presentation behavior",
    "Integrations, Jobs, and I/O": "integration, background job, or input/output behavior",
    "Error Handling and Observability": "error handling, logging, tracing, or monitoring",
    "Configuration and Bootstrapping": "configuration, registration, or startup behavior",
    "Build, Tooling, and Scripts": "build, command-line, or developer tooling behavior",
    "Utilities and Shared Helpers": "shared helper or reusable utility behavior",
    "Uncategorized Domain Logic": "domain behavior that needs source inspection",
}

STOP_TAGS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "function",
    "method",
    "class",
    "const",
    "let",
    "var",
    "def",
    "return",
    "public",
    "private",
    "protected",
    "static",
    "async",
    "void",
    "string",
    "number",
    "boolean",
    "object",
    "true",
    "false",
    "null",
    "none",
}


@dataclass
class CallableUnit:
    id: str
    name: str
    qualified_name: str
    kind: str
    language: str
    file: str
    line: int
    owner: str
    signature: str
    category: str
    purpose: str
    tags: list[str]


@dataclass
class FileRecord:
    file: str
    language: str
    callable_count: int
    dominant_category: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a categorized codebase callable tree.",
    )
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--output",
        help="Markdown output path. Defaults to <repo>/.codex/codebase-explore/codebase-tree.md.",
    )
    parser.add_argument(
        "--json-output",
        help="JSON output path. Defaults to <repo>/.codex/codebase-explore/codebase-tree.json.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories other than explicitly excluded names.",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to skip. Can be provided multiple times.",
    )
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="File glob to skip. Can be provided multiple times.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=1_500_000,
        help="Skip source files larger than this many bytes.",
    )
    return parser.parse_args(argv)


def posix_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def discover_source_files(
    root: Path,
    include_hidden: bool,
    exclude_dirs: Iterable[str],
    exclude_globs: Iterable[str],
    max_file_bytes: int,
) -> tuple[list[Path], list[str]]:
    excluded_dirs = set(DEFAULT_EXCLUDE_DIRS) | set(exclude_dirs)
    excluded_globs = set(DEFAULT_EXCLUDE_GLOBS) | set(exclude_globs)
    files: list[Path] = []
    skipped: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        kept_dirs = []
        for dirname in dirnames:
            if dirname in excluded_dirs:
                continue
            if not include_hidden and dirname.startswith("."):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            if not include_hidden and filename.startswith("."):
                continue
            path = current / filename
            rel = posix_rel(path, root)
            if path.suffix.lower() not in LANGUAGES:
                continue
            if any(fnmatch.fnmatch(filename, glob) or fnmatch.fnmatch(rel, glob) for glob in excluded_globs):
                skipped.append(rel)
                continue
            try:
                if path.stat().st_size > max_file_bytes:
                    skipped.append(rel)
                    continue
            except OSError:
                skipped.append(rel)
                continue
            files.append(path)

    return sorted(files), sorted(skipped)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def split_words(value: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    pieces = re.split(r"[^A-Za-z0-9]+", spaced.lower())
    return [piece for piece in pieces if piece]


def token_set(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        tokens.update(split_words(value))
    return tokens


def classify(rel: str, owner: str, name: str, signature: str) -> str:
    path_tokens = token_set(rel)
    name_tokens = token_set(owner, name)
    sig_tokens = token_set(signature)

    best_category = "Uncategorized Domain Logic"
    best_score = 0
    for category, keywords in CATEGORY_RULES:
        score = 0
        score += 4 * len(name_tokens & keywords)
        score += 3 * len(path_tokens & keywords)
        score += len(sig_tokens & keywords)
        if category == "Tests and Quality" and path_tokens & {"test", "tests"}:
            score += 6
        if score > best_score:
            best_category = category
            best_score = score
    return best_category


def infer_purpose(category: str, rel: str, owner: str, name: str) -> str:
    basis = []
    if owner:
        basis.append(f"owner `{owner}`")
    basis.append(f"name `{name}`")
    basis.append(f"path `{rel}`")
    return f"Likely {CATEGORY_PURPOSES[category]} based on " + ", ".join(basis) + "."


def tags_for(rel: str, owner: str, name: str, signature: str) -> list[str]:
    ordered = []
    seen = set()
    for token in split_words(" ".join([rel, owner, name, signature])):
        if token in STOP_TAGS or len(token) <= 1 or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
        if len(ordered) == 12:
            break
    return ordered


def clean_signature(line: str) -> str:
    signature = line.strip()
    signature = re.sub(r"\s+", " ", signature)
    signature = signature.rstrip("{").rstrip(";").rstrip(":").strip()
    return signature


def make_callable(
    *,
    rel: str,
    language: str,
    line: int,
    name: str,
    kind: str,
    owner: str = "",
    signature: str = "",
) -> CallableUnit:
    name = name.strip()
    owner = owner.strip(".")
    qualified_name = f"{owner}.{name}" if owner else name
    signature = signature or qualified_name
    category = classify(rel, owner, name, signature)
    return CallableUnit(
        id=f"{rel}:{line}:{qualified_name}",
        name=name,
        qualified_name=qualified_name,
        kind=kind,
        language=language,
        file=rel,
        line=line,
        owner=owner,
        signature=signature,
        category=category,
        purpose=infer_purpose(category, rel, owner, name),
        tags=tags_for(rel, owner, name, signature),
    )


def parse_python(text: str, rel: str, language: str) -> list[CallableUnit]:
    lines = text.splitlines()
    callables: list[CallableUnit] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return parse_regex_callables(text, rel, language)

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[tuple[str, str]] = []

        def owner(self) -> str:
            return ".".join(name for name, _kind in self.stack)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.stack.append((node.name, "class"))
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node, async_def=False)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node, async_def=True)

        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Lambda):
                for target in node.targets:
                    name = target_name(target)
                    if name:
                        signature = source_line(lines, node.lineno) or f"{name} = lambda"
                        callables.append(
                            make_callable(
                                rel=rel,
                                language=language,
                                line=node.lineno,
                                name=name,
                                kind="lambda",
                                owner=self.owner(),
                                signature=signature,
                            )
                        )
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if isinstance(node.value, ast.Lambda):
                name = target_name(node.target)
                if name:
                    signature = source_line(lines, node.lineno) or f"{name} = lambda"
                    callables.append(
                        make_callable(
                            rel=rel,
                            language=language,
                            line=node.lineno,
                            name=name,
                            kind="lambda",
                            owner=self.owner(),
                            signature=signature,
                        )
                    )
            self.generic_visit(node)

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, async_def: bool) -> None:
            owner = self.owner()
            in_class = any(kind == "class" for _name, kind in self.stack)
            kind = "method" if in_class else "function"
            if any(kind == "function" for _name, kind in self.stack):
                kind = "nested function"
            try:
                args = ast.unparse(node.args)
            except Exception:
                args = "..."
            prefix = "async def" if async_def else "def"
            signature = f"{prefix} {node.name}({args})"
            source = source_line(lines, node.lineno)
            if source:
                signature = clean_signature(source)
            callables.append(
                make_callable(
                    rel=rel,
                    language=language,
                    line=node.lineno,
                    name=node.name,
                    kind=kind,
                    owner=owner,
                    signature=signature,
                )
            )
            self.stack.append((node.name, "function"))
            self.generic_visit(node)
            self.stack.pop()

    Visitor().visit(tree)
    return callables


def target_name(target: ast.AST) -> str:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def source_line(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


CLASS_RE = re.compile(
    r"\b(?:class|interface|enum|record|object|struct|protocol|extension|trait|impl)\s+([A-Za-z_$][\w$]*)"
)

JS_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+default\s+|export\s+)?(?:async\s+)?function\s+\*?\s*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"
)
JS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
)
JS_FUNCTION_VALUE_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?function\b"
)
JS_CLASS_METHOD_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|get\s+|set\s+)*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*(?::\s*[^=]+)?\s*\{"
)
JS_OBJECT_METHOD_RE = re.compile(
    r"^\s*([A-Za-z_$][\w$]*)\s*:\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)"
)

JAVA_LIKE_METHOD_RE = re.compile(
    r"^\s*(?:(?:@\w+(?:\([^)]*\))?)\s*)*"
    r"(?P<modifiers>(?:(?:public|private|protected|internal|static|final|abstract|synchronized|native|default|strictfp|override|virtual|sealed|async|extern|unsafe|partial)\s+)*)"
    r"(?:<[^>]+>\s*)?"
    r"(?P<type>(?:(?:[\w$<>\[\],.?&:*]+)\s+)+)?"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\((?P<args>[^)]*)\)\s*(?:throws\s+[^{;]+)?(?:\{|;|=>)?\s*$"
)
JAVA_RECORD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final)\s+)*record\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"
)
KOTLIN_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|open|override|suspend|inline|tailrec|operator|infix|actual|expect)\s+)*"
    r"fun\s+(?:<[^>]+>\s*)?(?:(?:[A-Za-z_][\w.<>]*)\.)?([A-Za-z_][\w]*)\s*\(([^)]*)\)"
)
GO_FUNCTION_RE = re.compile(
    r"^\s*func\s+(?:\(([^)]*)\)\s*)?([A-Za-z_][\w]*)\s*\(([^)]*)\)"
)
RUBY_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][\w!?=]*)(?:\(([^)]*)\)|\s+([^#]*))?")
PHP_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|abstract)\s+)*function\s+&?\s*([A-Za-z_][\w]*)\s*\(([^)]*)\)"
)
RUST_FUNCTION_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)"
)
SWIFT_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:public|private|internal|fileprivate|open|static|class|mutating|override|final)\s+)*func\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)"
)
C_LIKE_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:static|inline|extern|virtual|constexpr|friend|template\s*<[^>]+>)\s+)*"
    r"(?:[A-Za-z_][\w:<>,~*&\s]+\s+)+([A-Za-z_~][\w:~]*)\s*\(([^)]*)\)\s*(?:const\s*)?(?:\{|;)\s*$"
)


def parse_regex_callables(text: str, rel: str, language: str) -> list[CallableUnit]:
    lines = text.splitlines()
    callables: list[CallableUnit] = []
    seen: set[tuple[int, str, str]] = set()
    owners: list[tuple[str, int]] = []
    brace_depth = 0

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        while owners and brace_depth < owners[-1][1]:
            owners.pop()

        if not stripped or stripped.startswith(("//", "#", "*")):
            brace_depth += brace_delta(line)
            continue

        class_match = CLASS_RE.search(stripped)
        class_name = class_match.group(1) if class_match and language not in {"Go", "Ruby"} else ""

        owner = ".".join(name for name, _depth in owners)
        candidates = candidates_for_line(stripped, language, owner)
        for name, kind in candidates:
            if not name or name in CONTROL_WORDS:
                continue
            key = (line_number, name, kind)
            if key in seen:
                continue
            seen.add(key)
            callables.append(
                make_callable(
                    rel=rel,
                    language=language,
                    line=line_number,
                    name=name,
                    kind=kind,
                    owner=owner_for_candidate(language, owner, stripped, kind),
                    signature=clean_signature(stripped),
                )
            )

        if class_name:
            owners.append((class_name, max(brace_depth + 1, 1)))
        brace_depth += brace_delta(line)

    return callables


def candidates_for_line(stripped: str, language: str, owner: str) -> list[tuple[str, str]]:
    if stripped.startswith(("return ", "throw ", "case ", "new ")):
        return []

    candidates: list[tuple[str, str]] = []
    js_like = language in {"JavaScript", "JavaScript React", "TypeScript", "TypeScript React", "Vue", "Svelte"}
    if js_like:
        for regex, kind in (
            (JS_FUNCTION_RE, "function"),
            (JS_ARROW_RE, "arrow function"),
            (JS_FUNCTION_VALUE_RE, "function value"),
            (JS_OBJECT_METHOD_RE, "object method"),
        ):
            match = regex.match(stripped)
            if match:
                candidates.append((match.group(1), kind))
        if owner:
            match = JS_CLASS_METHOD_RE.match(stripped)
            if match:
                candidates.append((match.group(1), "method"))
        return candidates

    if language in {"Java", "C#"}:
        record_match = JAVA_RECORD_RE.match(stripped) if language == "Java" else None
        if record_match:
            candidates.append((record_match.group(1), "record"))
            return candidates
        if stripped.startswith("@"):
            return []
        match = JAVA_LIKE_METHOD_RE.match(stripped)
        if match:
            name = match.group("name")
            owner_leaf = owner.split(".")[-1] if owner else ""
            has_declaration_marker = bool(match.group("modifiers")) or bool(match.group("type")) or name == owner_leaf
            if has_declaration_marker and name not in {"super", "this"}:
                candidates.append((name, "method" if owner else "function"))
        return candidates

    if language in {"Kotlin"}:
        match = KOTLIN_FUNCTION_RE.match(stripped)
        if match:
            candidates.append((match.group(1), "function"))
        return candidates

    if language == "Go":
        match = GO_FUNCTION_RE.match(stripped)
        if match:
            receiver = match.group(1) or ""
            kind = "method" if receiver else "function"
            candidates.append((match.group(2), kind))
        return candidates

    if language == "Ruby":
        match = RUBY_DEF_RE.match(stripped)
        if match:
            candidates.append((match.group(1), "method" if owner else "function"))
        return candidates

    if language == "PHP":
        match = PHP_FUNCTION_RE.match(stripped)
        if match:
            candidates.append((match.group(1), "method" if owner else "function"))
        return candidates

    if language == "Rust":
        match = RUST_FUNCTION_RE.match(stripped)
        if match:
            candidates.append((match.group(1), "function"))
        return candidates

    if language == "Swift":
        match = SWIFT_FUNCTION_RE.match(stripped)
        if match:
            candidates.append((match.group(1), "function"))
        return candidates

    if language in {"C", "C++", "C/C++ Header", "C++ Header"}:
        match = C_LIKE_FUNCTION_RE.match(stripped)
        if match:
            name = match.group(1).split("::")[-1]
            candidates.append((name, "function"))
        return candidates

    return candidates


def owner_for_candidate(language: str, owner: str, stripped: str, kind: str) -> str:
    if language == "Go" and kind == "method":
        match = GO_FUNCTION_RE.match(stripped)
        if match and match.group(1):
            receiver = match.group(1).strip().lstrip("*").split()
            return receiver[-1].lstrip("*") if receiver else owner
    return owner


def brace_delta(line: str) -> int:
    no_strings = re.sub(r'"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|`(?:\\.|[^`])*`', "", line)
    return no_strings.count("{") - no_strings.count("}")


def detect_callables(path: Path, root: Path) -> tuple[str, str, list[CallableUnit]]:
    rel = posix_rel(path, root)
    language = LANGUAGES[path.suffix.lower()]
    text = read_text(path)
    if language == "Python":
        return rel, language, parse_python(text, rel, language)
    return rel, language, parse_regex_callables(text, rel, language)


def dominant_category(callables: list[CallableUnit]) -> str:
    if not callables:
        return ""
    return Counter(callable.category for callable in callables).most_common(1)[0][0]


def build_markdown(
    *,
    root: Path,
    generated_at: str,
    files: list[FileRecord],
    callables: list[CallableUnit],
    skipped_files: list[str],
    files_without_callables: list[str],
) -> str:
    lines: list[str] = []
    category_counts = Counter(callable.category for callable in callables)
    language_counts = Counter(file.language for file in files)
    repeated = repeated_names(callables)

    lines.append("# Codebase Explore Tree")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Repository: `{root}`")
    lines.append(f"- Generated at: `{generated_at}`")
    lines.append(f"- Source files scanned: {len(files)}")
    lines.append(f"- Callables detected: {len(callables)}")
    lines.append(f"- Files without detected callables: {len(files_without_callables)}")
    lines.append(f"- Skipped source-like files: {len(skipped_files)}")
    lines.append("")
    lines.append("### Languages")
    lines.append("")
    append_counter(lines, language_counts)
    lines.append("")
    lines.append("### Categories")
    lines.append("")
    append_counter(lines, category_counts)
    lines.append("")

    lines.append("## Functional Category Tree")
    lines.append("")
    append_category_tree(lines, callables)
    lines.append("")

    lines.append("## Repository File Tree")
    lines.append("")
    append_file_tree(lines, files, callables)
    lines.append("")

    lines.append("## Repeated Callable Names")
    lines.append("")
    if repeated:
        for name, items in repeated:
            locations = ", ".join(f"`{item.file}:L{item.line}`" for item in items[:8])
            extra = "" if len(items) <= 8 else f", ... +{len(items) - 8} more"
            lines.append(f"- `{name}`: {len(items)} occurrences - {locations}{extra}")
    else:
        lines.append("- None detected.")
    lines.append("")

    lines.append("## Files Without Detected Callables")
    lines.append("")
    if files_without_callables:
        for rel in files_without_callables:
            lines.append(f"- `{rel}`")
    else:
        lines.append("- None.")
    lines.append("")

    if skipped_files:
        lines.append("## Skipped Source-Like Files")
        lines.append("")
        for rel in skipped_files:
            lines.append(f"- `{rel}`")
        lines.append("")

    lines.append("## Callable Catalog")
    lines.append("")
    if callables:
        lines.append("| Category | File | Line | Kind | Callable | Purpose |")
        lines.append("| --- | --- | ---: | --- | --- | --- |")
        for item in sorted(callables, key=lambda c: (c.category, c.file, c.line, c.qualified_name.lower())):
            lines.append(
                "| "
                + " | ".join(
                    [
                        escape_table(item.category),
                        f"`{item.file}`",
                        str(item.line),
                        escape_table(item.kind),
                        f"`{inline_code(item.signature)}`",
                        escape_table(item.purpose),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No callables detected.")
    lines.append("")
    return "\n".join(lines)


def append_counter(lines: list[str], counter: Counter[str]) -> None:
    if not counter:
        lines.append("- None.")
        return
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {key}: {count}")


def append_category_tree(lines: list[str], callables: list[CallableUnit]) -> None:
    if not callables:
        lines.append("- No callables detected.")
        return
    by_category: dict[str, list[CallableUnit]] = defaultdict(list)
    for item in callables:
        by_category[item.category].append(item)

    for category in CATEGORY_ORDER:
        items = by_category.get(category, [])
        if not items:
            continue
        lines.append(f"- {category} ({len(items)})")
        by_file: dict[str, list[CallableUnit]] = defaultdict(list)
        for item in items:
            by_file[item.file].append(item)
        for rel in sorted(by_file):
            file_items = sorted(by_file[rel], key=lambda c: (c.line, c.qualified_name.lower()))
            lines.append(f"  - `{rel}` ({len(file_items)})")
            for item in file_items:
                lines.append(f"    - {callable_bullet(item, include_category=False)}")


def append_file_tree(lines: list[str], files: list[FileRecord], callables: list[CallableUnit]) -> None:
    if not files:
        lines.append("- No source files scanned.")
        return
    callables_by_file: dict[str, list[CallableUnit]] = defaultdict(list)
    for item in callables:
        callables_by_file[item.file].append(item)

    tree: dict[str, object] = {}
    records = {file.file: file for file in files}
    for file in files:
        parts = file.file.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})  # type: ignore[assignment]
        node.setdefault("__files__", []).append(parts[-1])  # type: ignore[union-attr]

    render_tree_node(lines, tree, records, callables_by_file, indent=0, prefix="")


def render_tree_node(
    lines: list[str],
    node: dict[str, object],
    records: dict[str, FileRecord],
    callables_by_file: dict[str, list[CallableUnit]],
    indent: int,
    prefix: str,
) -> None:
    pad = "  " * indent
    dirs = sorted(key for key in node if key != "__files__")
    for dirname in dirs:
        lines.append(f"{pad}- `{dirname}/`")
        child = node[dirname]
        if isinstance(child, dict):
            render_tree_node(lines, child, records, callables_by_file, indent + 1, f"{prefix}{dirname}/")

    for filename in sorted(node.get("__files__", [])):  # type: ignore[arg-type]
        rel = f"{prefix}{filename}"
        record = records[rel]
        count = record.callable_count
        dominant = f"; dominant: {record.dominant_category}" if record.dominant_category else ""
        lines.append(f"{pad}- `{filename}` ({record.language}; {count} callables{dominant})")
        for item in sorted(callables_by_file.get(rel, []), key=lambda c: (c.line, c.qualified_name.lower())):
            lines.append(f"{pad}  - {callable_bullet(item, include_category=True)}")


def callable_bullet(item: CallableUnit, include_category: bool) -> str:
    signature = truncate(inline_code(item.signature), 150)
    metadata = f"{item.kind}; {item.language}"
    if include_category:
        metadata += f"; {item.category}"
    return f"L{item.line} `{signature}` [{metadata}] - {item.purpose}"


def repeated_names(callables: list[CallableUnit]) -> list[tuple[str, list[CallableUnit]]]:
    groups: dict[str, list[CallableUnit]] = defaultdict(list)
    for item in callables:
        groups[item.name].append(item)
    repeated = [(name, items) for name, items in groups.items() if len(items) > 1]
    return sorted(repeated, key=lambda entry: (-len(entry[1]), entry[0].lower()))


def inline_code(value: str) -> str:
    return value.replace("`", "'")


def escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def write_outputs(
    *,
    root: Path,
    output: Path,
    json_output: Path,
    files: list[FileRecord],
    callables: list[CallableUnit],
    skipped_files: list[str],
    files_without_callables: list[str],
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    markdown = build_markdown(
        root=root,
        generated_at=generated_at,
        files=files,
        callables=callables,
        skipped_files=skipped_files,
        files_without_callables=files_without_callables,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    payload = {
        "repository": str(root),
        "generated_at": generated_at,
        "summary": {
            "files_scanned": len(files),
            "callables_detected": len(callables),
            "files_without_detected_callables": len(files_without_callables),
            "skipped_source_like_files": len(skipped_files),
            "languages": dict(sorted(Counter(file.language for file in files).items())),
            "categories": dict(sorted(Counter(item.category for item in callables).items())),
        },
        "callables": [asdict(item) for item in sorted(callables, key=lambda c: (c.file, c.line, c.qualified_name))],
        "files": [asdict(file) for file in files],
        "repeated_callable_names": [
            {
                "name": name,
                "occurrences": len(items),
                "locations": [
                    {"file": item.file, "line": item.line, "qualified_name": item.qualified_name}
                    for item in items
                ],
            }
            for name, items in repeated_names(callables)
        ],
        "files_without_detected_callables": files_without_callables,
        "skipped_source_like_files": skipped_files,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.repo).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Repository path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    default_dir = root / ".codex" / "codebase-explore"
    output = Path(args.output).expanduser().resolve() if args.output else default_dir / "codebase-tree.md"
    json_output = (
        Path(args.json_output).expanduser().resolve()
        if args.json_output
        else default_dir / "codebase-tree.json"
    )

    source_files, skipped_files = discover_source_files(
        root=root,
        include_hidden=args.include_hidden,
        exclude_dirs=args.exclude_dir,
        exclude_globs=args.exclude_glob,
        max_file_bytes=args.max_file_bytes,
    )

    all_callables: list[CallableUnit] = []
    file_records: list[FileRecord] = []
    files_without_callables: list[str] = []
    for path in source_files:
        rel, language, callables = detect_callables(path, root)
        all_callables.extend(callables)
        if not callables:
            files_without_callables.append(rel)
        file_records.append(
            FileRecord(
                file=rel,
                language=language,
                callable_count=len(callables),
                dominant_category=dominant_category(callables),
            )
        )

    file_records.sort(key=lambda record: record.file)
    all_callables.sort(key=lambda item: (item.file, item.line, item.qualified_name.lower()))
    write_outputs(
        root=root,
        output=output,
        json_output=json_output,
        files=file_records,
        callables=all_callables,
        skipped_files=skipped_files,
        files_without_callables=files_without_callables,
    )
    print(f"Wrote Markdown tree: {output}")
    print(f"Wrote JSON index: {json_output}")
    print(f"Scanned {len(file_records)} source files; detected {len(all_callables)} callables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
