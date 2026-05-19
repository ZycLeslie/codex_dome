---
name: explore-codebase-tree
description: Exhaustively explore a code repository by scanning callable units such as functions, methods, constructors, handlers, hooks, jobs, tests, and comparable entry points, then generate a tree-style Markdown map and JSON index grouped by functional category and file path. Use when Codex needs to understand an unfamiliar repository, list every method before design or refactoring, classify existing logic by feature responsibility, produce a codebase exploration artifact, or create an implementation-ready method inventory before changing code.
---

# Explore Codebase Tree

Build a concrete repository map before designing, refactoring, or adding behavior. The goal is to leave behind an artifact that another engineer or agent can use as a landing map: every detected callable, grouped by what it appears to do and where it lives.

## Quick Start

1. Treat the current workspace as the target repo unless the user gives another path.
2. Run the bundled scanner:
   `python3 .codex/skills/explore-codebase-tree/scripts/explore_codebase_tree.py .`
3. Open the Markdown output:
   `.codex/codebase-explore/codebase-tree.md`
4. Use the category tree first, then inspect source files for any callable that looks relevant.

Use explicit paths when needed:

`python3 .codex/skills/explore-codebase-tree/scripts/explore_codebase_tree.py <repo> --output <tree.md> --json-output <tree.json>`

## Workflow

### 1. Scope the exploration

- Scan the whole repo by default.
- Narrow scope only when the user asks for a subsystem, package, or directory.
- Prefer a fresh scan when code may have changed.
- Keep generated artifacts in `.codex/codebase-explore/` unless the user asks for another destination.

### 2. Generate the tree and index

The scanner uses Python standard library parsing plus language-specific regex heuristics, so it runs without installing dependencies. It detects common callable forms across Python, JavaScript, TypeScript, Java, Kotlin, Go, Ruby, PHP, C#, C/C++, Rust, and Swift.

Useful options:

- `--include-hidden`: include hidden directories skipped by default.
- `--exclude-dir NAME`: skip another directory name.
- `--exclude-glob PATTERN`: skip matching files, for example `--exclude-glob '*.min.js'`.
- `--max-file-bytes N`: adjust the per-file scan limit.

### 3. Read the output as an implementation map

Read sections in this order:

- `Summary`: total files, callables, languages, and categories.
- `Functional Category Tree`: method/function tree grouped by inferred responsibility.
- `Repository File Tree`: same methods under their source paths.
- `Repeated Callable Names`: duplicate names that may hide overlap or framework conventions.
- `Files Without Detected Callables`: files that may still matter for config, templates, assets, or data.
- `JSON Index`: use for scripted filtering or follow-up automation.

### 4. Verify source before acting

The tree is an index, not a substitute for reading code.

- Open the listed source file and line before reusing or modifying a callable.
- Check callers, side effects, error handling, and tests.
- Treat categories as navigation hints; reclassify mentally if path/name context proves otherwise.
- When implementing, mention the searched category, file, and method names that influenced the plan.

## Classification

The scanner assigns one primary category using path parts, owner/class names, method names, and signature words:

- Tests and Quality
- API, Routing, and Controllers
- Auth and Security
- Validation, Parsing, and Mapping
- Data Access and Persistence
- Business Services and Workflows
- UI and Presentation
- Integrations, Jobs, and I/O
- Error Handling and Observability
- Configuration and Bootstrapping
- Build, Tooling, and Scripts
- Utilities and Shared Helpers
- Uncategorized Domain Logic

Use categories for navigation, not as truth. A `handleSubmit` in a UI file and a `handleSubmit` in a controller may land in different categories because path context matters.

## Output Contract

When the user asks for a codebase explore artifact, provide or reference the generated Markdown tree and JSON index. If the repo is large, summarize the highest-signal categories and repeated names in the chat while leaving the full artifact on disk.

For a stricter example of the expected tree shape and JSON fields, read `references/output-contract.md`.
