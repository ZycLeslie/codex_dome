---
name: index-repo-methods
description: Scan a code repository to extract functions, methods, handlers, constructors, and comparable callable units, then generate categorized Markdown and JSON method inventories for AI-assisted design, refactoring, and development. Use when Codex needs to discover existing repository logic before adding features, avoid duplicate implementations, produce a method/file checklist, audit reusable helpers or services, or refresh a searchable codebase method index.
---

# Index Repo Methods

Generate a repository method inventory before designing or implementing logic that may already exist.

## Quick Start

1. Treat the current workspace as the repository unless the user gives another path.
2. Run the bundled script:
   `python3 .codex/skills/index-repo-methods/scripts/index_methods.py .`
3. Open the generated Markdown inventory:
   `.codex/method-index/methods.md`
4. Search the inventory first by domain words, feature names, data model names, and operation verbs.
5. If a likely existing method is found, inspect the source file before writing new logic.

Use explicit output paths when needed:

`python3 .codex/skills/index-repo-methods/scripts/index_methods.py <repo> --output <methods.md> --json-output <methods.json>`

## Workflow

### 1. Generate or refresh the inventory

- Prefer a fresh scan when the code may have changed.
- Keep the default JSON output; it is useful for scripted filtering and duplicate-name checks.
- The script uses standard library parsing and regex heuristics, so it works without installing dependencies.
- Default scanning includes source and test files, while skipping heavy generated/vendor directories such as `.git`, `.codex`, `node_modules`, `dist`, `build`, `coverage`, `.venv`, and `target`.

Useful options:

- `--include-hidden`: include hidden directories that are skipped by default.
- `--exclude-dir NAME`: skip another directory name.
- `--exclude-glob PATTERN`: skip matching files, for example `--exclude-glob '*.min.js'`.
- `--max-file-bytes N`: raise or lower the per-file scan limit.

### 2. Use the Markdown inventory as a lookup map

Read these sections first:

- `Summary`: category counts and broad system shape.
- `File Checklist`: files with method counts and dominant categories.
- Category sections: grouped method list with file, line, owner, signature, and inferred purpose.
- `Repeated Method Names`: names that appear in multiple places and may hide duplicate logic.

When designing:

- Search for nouns from the requirement, data model names, endpoint names, and domain terms.
- Search for verbs such as `validate`, `parse`, `create`, `update`, `sync`, `fetch`, `calculate`, `render`, and `handle`.
- Prefer extending a nearby existing service/helper/controller when category, owner, and signature match the new need.
- If no match exists, note the searched terms before adding new logic.

### 3. Verify source before reuse

The inventory is an index, not a substitute for reading code.

- Open the listed file and line.
- Check callers, side effects, error handling, and tests.
- Confirm whether similar repeated names are intentional overloads, framework hooks, or real duplication.

## Classification

The script assigns one primary category using path, owner, method name, and signature keywords:

- Tests
- API, Routing, and Controllers
- Auth and Security
- Validation, Parsing, and Mapping
- Data Access and Persistence
- Business Services and Workflows
- UI and Presentation
- Integrations, Jobs, and I/O
- Error Handling and Logging
- Configuration and Bootstrapping
- Utilities and Shared Helpers
- Uncategorized

Treat categories as navigation hints. If a method is misclassified, rely on the file path, owner, and signature.

## Output Expectations

Return or reference the generated method inventory when the user asks for the repository method list. For development tasks, summarize only the relevant existing methods and explain how they affect the implementation plan.

If the repository is very large, generate the full files, then inspect the highest-signal categories and repeated-name section instead of pasting the entire inventory into the conversation.
