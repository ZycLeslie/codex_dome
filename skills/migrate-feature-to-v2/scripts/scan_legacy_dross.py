#!/usr/bin/env python3
"""Scan target code for legacy implementation details copied during migration."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".ai-migrations",
    ".git",
    ".idea",
    ".next",
    ".pytest_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}

TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".gradle",
    ".graphql",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".kts",
    ".md",
    ".php",
    ".properties",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

RULES = [
    (
        "absolute-posix-path",
        "high",
        re.compile(r"(?<![\w.])/(Users|home|private|var|opt|tmp|data|mnt|Volumes|srv)/[A-Za-z0-9._~@%+=,:/\-]+"),
        "Replace legacy filesystem paths with target configuration, storage abstraction, or repo-relative resources.",
    ),
    (
        "windows-absolute-path",
        "high",
        re.compile(r"[A-Za-z]:\\+[A-Za-z0-9._~ @%+=,:\\\-]+"),
        "Replace legacy Windows paths with target configuration or path abstraction.",
    ),
    (
        "file-url",
        "high",
        re.compile(r"file:///[A-Za-z0-9._~@%+=,:/\-]+"),
        "Avoid file:// legacy paths in target code; use target storage/configuration conventions.",
    ),
    (
        "hard-coded-localhost-url",
        "medium",
        re.compile(r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:[0-9]+)?(/[A-Za-z0-9._~@%+=,:/?#&\-]*)?"),
        "Use target environment configuration or test fixtures instead of hard-coded local endpoints.",
    ),
    (
        "probable-fully-qualified-name",
        "medium",
        re.compile(r"\b[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){3,}\.[A-Z][A-Za-z0-9_]*\b"),
        "Review fully qualified names copied from source; prefer target imports, adapters, or target-owned interfaces.",
    ),
]


@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    excerpt: str
    recommendation: str


def read_text(path: Path, limit: int) -> str | None:
    try:
        if path.stat().st_size > limit:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {
        "Dockerfile",
        "Makefile",
        "Procfile",
    }


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS)
        directory_path = Path(directory)
        for filename in sorted(filenames):
            path = directory_path / filename
            if is_text_candidate(path):
                files.append(path)
    return files


def excerpt(line: str, start: int, end: int, max_len: int = 180) -> str:
    value = line.strip()
    if len(value) <= max_len:
        return value
    center = max(0, start - max_len // 3)
    sliced = value[center : center + max_len]
    prefix = "..." if center else ""
    suffix = "..." if center + max_len < len(value) else ""
    return prefix + sliced + suffix


def build_token_rules(tokens: list[str]) -> list[tuple[str, str, re.Pattern[str], str]]:
    rules = []
    for index, token in enumerate(tokens, start=1):
        stripped = token.strip()
        if not stripped:
            continue
        pattern = re.compile(re.escape(stripped))
        rules.append(
            (
                f"legacy-token-{index}",
                "high",
                pattern,
                "Legacy-specific token found in target code; map it to target naming/configuration or document explicit compatibility.",
            )
        )
    return rules


def scan(root: Path, tokens: list[str], limit: int) -> list[Finding]:
    findings: list[Finding] = []
    all_rules = [*RULES, *build_token_rules(tokens)]
    for path in iter_files(root):
        text = read_text(path, limit)
        if text is None:
            continue
        rel = path.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule, severity, pattern, recommendation in all_rules:
                for match in pattern.finditer(line):
                    findings.append(
                        Finding(
                            rule=rule,
                            severity=severity,
                            path=rel,
                            line=line_number,
                            excerpt=excerpt(line, match.start(), match.end()),
                            recommendation=recommendation,
                        )
                    )
    return findings


def render_markdown(root: Path, findings: list[Finding]) -> str:
    lines = [
        "# Legacy Dross Scan",
        "",
        f"- Target root: `{root}`",
        f"- Findings: {len(findings)}",
        "",
    ]
    if not findings:
        lines.extend(["No suspicious legacy implementation details found.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Severity | Rule | Location | Excerpt | Recommendation |",
            "|---|---|---|---|---|",
        ]
    )
    for finding in findings:
        location = f"{finding.path}:{finding.line}"
        excerpt_value = finding.excerpt.replace("|", "\\|")
        recommendation = finding.recommendation.replace("|", "\\|")
        lines.append(
            f"| {finding.severity} | `{finding.rule}` | `{location}` | `{excerpt_value}` | {recommendation} |"
        )
    lines.append("")
    lines.append("Review each finding before declaring migration complete. Preserve only items explicitly required by compatibility; otherwise adapt them to target conventions.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="Target repository or subdirectory to scan")
    parser.add_argument("--legacy-token", action="append", default=[], help="Source-specific package, path, domain, or prefix that must not leak into target code")
    parser.add_argument("--output-md", type=Path, help="Write Markdown report")
    parser.add_argument("--output-json", type=Path, help="Write JSON report")
    parser.add_argument("--max-file-size", type=int, default=1_000_000, help="Skip files larger than this many bytes")
    parser.add_argument(
        "--fail-on",
        choices=["none", "any", "medium", "high"],
        default="none",
        help="Exit with status 1 when findings at or above this severity exist",
    )
    return parser.parse_args()


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "any":
        return bool(findings)
    if fail_on == "medium":
        return any(item.severity in {"medium", "high"} for item in findings)
    if fail_on == "high":
        return any(item.severity == "high" for item in findings)
    return False


def main() -> int:
    args = parse_args()
    root = args.target.expanduser().resolve()
    if not root.is_dir():
        print(f"error: target is not a directory: {root}", file=sys.stderr)
        return 2

    findings = scan(root, args.legacy_token, args.max_file_size)
    markdown = render_markdown(root, findings)

    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown, encoding="utf-8")
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps([asdict(item) for item in findings], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    if not args.output_md and not args.output_json:
        print(markdown)

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
