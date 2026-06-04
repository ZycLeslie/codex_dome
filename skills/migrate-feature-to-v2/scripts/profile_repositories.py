#!/usr/bin/env python3
"""Create a lightweight, dependency-free profile of source and target repositories."""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


EXCLUDED_DIRS = {
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

LANGUAGES = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "Makefile",
    "Package.swift",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
    "settings.gradle",
    "settings.gradle.kts",
}

CONVENTION_NAMES = {
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CLAUDE.md",
    "CODEX.md",
    "CONTRIBUTING.md",
    "DEVELOPMENT.md",
    "README.md",
    "README",
}

FRAMEWORK_SIGNALS = {
    "Spring": ("spring-boot", "org.springframework"),
    "React": ('"react"', "'react'"),
    "Next.js": ('"next"', "'next'"),
    "Vue": ('"vue"', "'vue'"),
    "Angular": ("@angular/",),
    "Express": ('"express"', "'express'"),
    "NestJS": ("@nestjs/",),
    "Django": ("django",),
    "FastAPI": ("fastapi",),
    "Flask": ("flask",),
    "Rails": ("rails",),
    "ASP.NET": ("microsoft.aspnetcore",),
    "JUnit": ("junit",),
    "pytest": ("pytest",),
}

SAFE_TASK_PATTERN = re.compile(
    r"(^|[-_:])(build|check|compile|format|lint|test|typecheck|verify)([-_:]|$)",
    re.IGNORECASE,
)


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_test_file(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "test" in lowered_parts
        or "tests" in lowered_parts
        or "__tests__" in lowered_parts
        or name.startswith("test_")
        or name.endswith(("_test.go", "test.java", "tests.java", ".test.js", ".test.ts", ".spec.js", ".spec.ts"))
    )


def read_small_text(path: Path, limit: int = 1_000_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def package_scripts(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in sorted(scripts.items())[:40]}


def make_targets(path: Path) -> list[str]:
    targets: list[str] = []
    for line in read_small_text(path).splitlines():
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?:\s|$)", line)
        if match and not match.group(1).startswith("."):
            targets.append(match.group(1))
    return sorted(set(targets))[:40]


def is_safe_task(name: str) -> bool:
    return bool(SAFE_TASK_PATTERN.search(name))


def command_in(directory: Path, command: str) -> str:
    if directory == Path("."):
        return command
    return f"cd {directory.as_posix()} && {command}"


def build_hints(root: Path, manifests: list[str]) -> dict[str, Any]:
    hints: dict[str, Any] = {"commands": [], "package_scripts": {}, "make_targets": {}}
    commands: list[str] = hints["commands"]

    for manifest in manifests:
        relative_manifest = Path(manifest)
        directory = relative_manifest.parent
        path = root / relative_manifest
        filename = relative_manifest.name

        if filename == "package.json":
            scripts = package_scripts(path)
            hints["package_scripts"][manifest] = scripts
            commands.extend(command_in(directory, f"npm run {name}") for name in scripts if is_safe_task(name))
        elif filename == "pom.xml":
            wrapper = root / directory / "mvnw"
            commands.append(command_in(directory, "./mvnw test" if wrapper.exists() else "mvn test"))
        elif filename in {"build.gradle", "build.gradle.kts"}:
            wrapper = root / directory / "gradlew"
            commands.append(command_in(directory, "./gradlew test" if wrapper.exists() else "gradle test"))
        elif filename == "Cargo.toml":
            commands.append(command_in(directory, "cargo test"))
        elif filename == "go.mod":
            commands.append(command_in(directory, "go test ./..."))
        elif filename in {"pyproject.toml", "requirements.txt"}:
            commands.append(command_in(directory, "pytest"))
        elif filename == "Makefile":
            targets = make_targets(path)
            hints["make_targets"][manifest] = targets
            commands.extend(command_in(directory, f"make {target}") for target in targets if is_safe_task(target))

    hints["package_scripts"] = {key: value for key, value in hints["package_scripts"].items() if value}
    hints["make_targets"] = {key: value for key, value in hints["make_targets"].items() if value}
    hints["commands"] = list(dict.fromkeys(commands))[:80]
    return hints


def profile(root: Path, role: str) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"{role} repository is not a directory: {root}")

    language_counts: collections.Counter[str] = collections.Counter()
    top_dirs: collections.Counter[str] = collections.Counter()
    files: list[Path] = []
    manifests: list[str] = []
    conventions: list[str] = []
    ci_files: list[str] = []
    test_files: list[str] = []
    signal_texts: list[str] = []

    for directory, dirnames, filenames in __import__("os").walk(root):
        directory_path = Path(directory)
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS)
        for filename in sorted(filenames):
            path = directory_path / filename
            rel = relative(path, root)
            files.append(path)
            if len(path.relative_to(root).parts) > 1:
                top_dirs[path.relative_to(root).parts[0]] += 1
            language = LANGUAGES.get(path.suffix.lower())
            if language:
                language_counts[language] += 1
            if filename in MANIFEST_NAMES:
                manifests.append(rel)
                signal_texts.append(read_small_text(path).lower())
            if filename in CONVENTION_NAMES:
                conventions.append(rel)
            if rel.startswith(".github/workflows/") or rel.startswith(".gitlab-ci") or filename in {
                "Jenkinsfile",
                "azure-pipelines.yml",
                "azure-pipelines.yaml",
            }:
                ci_files.append(rel)
            if is_test_file(path.relative_to(root)):
                test_files.append(rel)

    joined_signals = "\n".join(signal_texts)
    frameworks = [
        name
        for name, patterns in FRAMEWORK_SIGNALS.items()
        if any(pattern.lower() in joined_signals for pattern in patterns)
    ]
    status = run_git(root, "status", "--short")
    git_info = {
        "is_repository": run_git(root, "rev-parse", "--is-inside-work-tree") == "true",
        "branch": run_git(root, "branch", "--show-current"),
        "commit": run_git(root, "rev-parse", "--short", "HEAD"),
        "dirty_file_count": len(status.splitlines()) if status else 0,
    }

    return {
        "role": role,
        "root": str(root),
        "git": git_info,
        "file_count": len(files),
        "languages": dict(language_counts.most_common()),
        "framework_signals": frameworks,
        "manifests": sorted(manifests),
        "build_hints": build_hints(root, sorted(manifests)),
        "test_file_count": len(test_files),
        "test_file_examples": sorted(test_files)[:30],
        "ci_files": sorted(ci_files)[:30],
        "convention_files": sorted(conventions)[:40],
        "largest_top_level_directories": [
            {"path": name, "file_count": count} for name, count in top_dirs.most_common(20)
        ],
    }


def markdown_list(items: list[str], empty: str = "None detected") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Repository Migration Profile",
        "",
        "| Role | Root | Branch | Commit | Dirty files | Files | Tests |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for item in data["repositories"]:
        git_info = item["git"]
        lines.append(
            f"| {item['role']} | `{item['root']}` | `{git_info['branch'] or '-'}` | "
            f"`{git_info['commit'] or '-'}` | {git_info['dirty_file_count']} | "
            f"{item['file_count']} | {item['test_file_count']} |"
        )

    for item in data["repositories"]:
        lines.extend(
            [
                "",
                f"## {item['role'].title()} Repository",
                "",
                "### Languages",
                "",
                "| Language | Files |",
                "|---|---:|",
            ]
        )
        if item["languages"]:
            lines.extend(f"| {name} | {count} |" for name, count in item["languages"].items())
        else:
            lines.append("| None detected | 0 |")
        lines.extend(
            [
                "",
                "### Framework Signals",
                "",
                markdown_list(item["framework_signals"]),
                "",
                "### Manifests",
                "",
                markdown_list(item["manifests"]),
                "",
                "### Candidate Build And Test Commands",
                "",
                markdown_list(item["build_hints"]["commands"]),
                "",
                "### Repository Guidance And CI",
                "",
                markdown_list(item["convention_files"] + item["ci_files"]),
                "",
                "### Test File Examples",
                "",
                markdown_list(item["test_file_examples"]),
            ]
        )
    lines.append("")
    lines.append("Use this profile for orientation only; verify feature behavior in source files and tests.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Local legacy source repository")
    parser.add_argument("--target", required=True, type=Path, help="Local 2.0 target repository")
    parser.add_argument("--output-dir", type=Path, help="Write repo-profile.md and repo-profile.json here")
    parser.add_argument("--markdown", type=Path, help="Write Markdown profile to this path")
    parser.add_argument("--json-output", type=Path, help="Write JSON profile to this path")
    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        data = {
            "repositories": [
                profile(args.source, "source"),
                profile(args.target, "target"),
            ]
        }
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    markdown = render_markdown(data)
    markdown_path = args.markdown
    json_path = args.json_output
    if args.output_dir:
        markdown_path = markdown_path or args.output_dir / "repo-profile.md"
        json_path = json_path or args.output_dir / "repo-profile.json"

    if markdown_path:
        write_text(markdown_path, markdown)
    if json_path:
        write_text(json_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    if not markdown_path and not json_path:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
