#!/usr/bin/env python3
"""Initialize a project-local migration workspace for migrate-feature-to-v2."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path


PHASES = [
    "repository-context",
    "source-exploration",
    "design-reconciliation",
    "design-approval",
    "implementation",
    "verification",
    "completion",
]

SURFACES = [
    "frontend",
    "backend-api",
    "job-event",
    "integration",
    "data",
    "config",
    "observability",
    "end-to-end",
]


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if slug:
        return slug[:80].strip("-")
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"feature-{digest}"


def write_if_needed(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def markdown_list(items: list[str]) -> str:
    if not items:
        return "- none\n"
    return "".join(f"- {item}\n" for item in items)


def build_templates(args: argparse.Namespace, root: Path, slug: str) -> dict[Path, str]:
    timestamp = now()
    feature = args.feature
    source = args.source or "unknown"
    target = str(args.target)
    design_docs = args.design_doc or []

    artifact_rows = [
        ("README.md", "Visual dashboard and quick links", "initialized"),
        ("migration-status.md", "Phase, surface, package, approval, and verification status", "initialized"),
        ("artifact-index.md", "Index of migration artifacts and ownership", "initialized"),
        ("timeline.md", "Append-only migration event timeline", "initialized"),
        ("resume.md", "Restart instructions and canonical reload set", "initialized"),
        ("migration-record.md", "Evidence-backed migration record", "pending"),
        ("migration-design.md", "Approval-ready migration design", "pending"),
        ("design-approval.md", "Implementation approval record", "pending"),
        ("source-exploration/source-exploration.md", "Source behavior baseline", "pending"),
        ("source-exploration/source-evidence.json", "Machine-readable evidence index", "pending"),
        ("source-exploration/feature-point-index.md", "Feature point navigation map", "pending"),
        ("source-exploration/legacy-smells.md", "Legacy smell and dross inventory", "pending"),
        ("orchestration/task-package-index.md", "Task package ledger", "pending"),
        ("orchestration/task-checklist.md", "Package status and lost-function guard", "pending"),
        ("orchestration/context-recovery.md", "Context recovery ledger", "pending"),
        ("orchestration/completion-check.md", "Final completion gate", "pending"),
    ]

    phase_rows = "\n".join(
        f"| {phase} | pending | main-agent |  |  |" for phase in PHASES
    )
    surface_rows = "\n".join(
        f"| {surface} | unknown | pending |  |  |" for surface in SURFACES
    )
    artifact_index_rows = "\n".join(
        f"| `{path}` | {purpose} | {status} | unassigned | {timestamp} |"
        for path, purpose, status in artifact_rows
    )
    quick_links = "\n".join(f"- [`{path}`](./{path})" for path, _, _ in artifact_rows[:8])

    evidence_json = {
        "feature": slug,
        "source": {
            "repository": source,
            "accessMethod": "unknown",
            "ref": "unknown",
        },
        "evidence": [],
    }

    return {
        root / "README.md": f"""# {feature} Migration Workspace

## Dashboard
| Item | Status |
|---|---|
| Feature | {feature} |
| Slug | `{slug}` |
| Source | {source} |
| Target | {target} |
| Current gate | repository-context |
| Current active package | none |
| Next action | Confirm repository roles, design inputs, feature surfaces, and task split. |
| Last updated | {timestamp} |

## Quick Links
{quick_links}

## Design Documents
{markdown_list(design_docs)}

## Working Rule
This folder is the source of truth for migration progress. After interruption or context compression, read `resume.md`, `migration-status.md`, `artifact-index.md`, `orchestration/task-checklist.md`, and the current task package before continuing.
""",
        root / "migration-status.md": f"""# {feature} Migration Status

## Phase Board
| Phase | Status | Owner | Evidence | Next action |
|---|---|---|---|---|
{phase_rows}

## Surface Board
| Surface | Present? | Status | Evidence | Notes |
|---|---|---|---|---|
{surface_rows}

## Feature Point Coverage
| Feature point | Surface | Artifact | Status | Gap |
|---|---|---|---|---|

## Package Board
| Package | Surface | One-pass feasibility | Status | Owner | Artifact |
|---|---|---|---|---|---|

## Approval Board
| Decision | Status | Evidence | Blocks |
|---|---|---|---|

## Verification Board
| Scenario or command | Status | Evidence | Gap |
|---|---|---|---|
""",
        root / "artifact-index.md": f"""# {feature} Artifact Index

| Artifact | Purpose | Status | Owner | Last updated |
|---|---|---|---|---|
{artifact_index_rows}
""",
        root / "timeline.md": f"""# {feature} Migration Timeline

| Time | Event | Actor | Evidence |
|---|---|---|---|
| {timestamp} | Migration workspace initialized | init_migration_workspace.py | `README.md` |
""",
        root / "resume.md": f"""# {feature} Resume

## Read First
1. `README.md`
2. `migration-status.md`
3. `artifact-index.md`
4. `orchestration/task-checklist.md`
5. Current package from the checklist, if any

## Latest Checkpoint
- Last updated: {timestamp}
- Current phase: repository-context
- Current active package: none
- Next action: confirm repository roles, design inputs, feature surfaces, and task split.
- Blockers: none recorded

## Canonical Reload Set
| Artifact | Why reload |
|---|---|
| `README.md` | Dashboard and current gate |
| `migration-status.md` | Visual progress status |
| `artifact-index.md` | Artifact locations and staleness |
| `orchestration/task-checklist.md` | Package state and lost-function guard |
| `source-exploration/feature-point-index.md` | Feature point navigation after exploration |
| `migration-design.md` | Approved or pending target design |
| `design-approval.md` | Approval status before implementation |
| `migration-record.md` | Evidence-backed decision ledger |

## Do Not Reload Broad Context Until
- The current task package names the required source, target, and design artifacts.
- The package one-pass feasibility is `yes` or explicitly accepted as `risky`.
""",
        root / "source-exploration" / "source-exploration.md": f"""# {feature} Source Exploration

## Source Access
- Repository: {source}
- Access method: unknown
- Branch/ref/commit: unknown
- Exploration timestamp: {timestamp}

## Entry Points
| Entry point | Type | Evidence | Notes |
|---|---|---|---|

## Surface Coverage
| Surface | Present? | Evidence | Feature points | Notes |
|---|---|---|---|---|

## Behavior Baseline
| Scenario | Inputs/triggers | Outputs/results | Side effects | Evidence |
|---|---|---|---|---|

## Implementation Trace
| Layer/responsibility | Files/symbols | Callers/callees | Evidence |
|---|---|---|---|

## Data And Integration Evidence
| Concern | Evidence | Notes |
|---|---|---|

## Essence And Dross
| Item | Classification | Evidence | Migration decision |
|---|---|---|---|

## Implementation Detail Dross
| Source-specific token/path/prefix | Type | Evidence | Target replacement or decision |
|---|---|---|---|

## Legacy Smells
| Smell | Severity | Evidence | Migration decision |
|---|---|---|---|

## Open Questions
| Question | Why it matters | Proposed next step |
|---|---|---|
""",
        root / "source-exploration" / "source-evidence.json": json.dumps(
            evidence_json, indent=2, ensure_ascii=False
        )
        + "\n",
        root / "source-exploration" / "feature-point-index.md": f"""# {feature} Feature Point Index

## Overview
- Source: {source}
- Ref: unknown
- Feature: {feature}

## Feature Points
| ID | Surface | Feature point | Markdown file | Status | Notes |
|---|---|---|---|---|---|

## Design Inputs
| Topic | Surface | Feature point files | Design impact |
|---|---|---|---|

## Open Questions
| Question | Related feature points | Decision needed |
|---|---|---|
""",
        root / "source-exploration" / "legacy-smells.md": f"""# {feature} Legacy Smells

## Summary
- Overall risk: unknown
- Scope checked: none yet

## Smell Inventory
| Smell/problem | Classification | Source evidence | Target decision | Verification |
|---|---|---|---|---|

## Implementation Detail Dross
| Token/path/prefix | Type | Source evidence | Target decision | Scan status |
|---|---|---|---|---|

## Deferred Items
| Item | Reason deferred | Risk | Follow-up |
|---|---|---|---|
""",
        root / "orchestration" / "task-package-index.md": f"""# {feature} Task Package Index

## Overview
- Feature: {feature}
- Source: {source}
- Target: {target}
- Current active package: none

## Packages
| Package ID | Role | Scope | One-pass feasibility | Inputs | Outputs | Status | Notes |
|---|---|---|---|---|---|---|---|

## Dependencies
| Package | Depends on | Reason |
|---|---|---|

## Approval Or Gate Status
| Package | Gate | Status | Evidence |
|---|---|---|---|
""",
        root / "orchestration" / "task-checklist.md": f"""# {feature} Task Checklist

## Summary
- Feature: {feature}
- Current active package: none
- Last updated: {timestamp}
- Completion check: not started

## Tasks
| Package | Surface | Objective | One-pass feasibility | Depends on | Status | Owner | Artifacts | Verification | Final check |
|---|---|---|---|---|---|---|---|---|---|

## Lost-Function Guard
| Feature point/surface | Covered by packages | Verified? | Gap |
|---|---|---|---|

## Deferred Or Blocked
| Task | Reason | Approval/evidence | Follow-up |
|---|---|---|---|
""",
        root / "orchestration" / "context-recovery.md": f"""# {feature} Context Recovery

## Canonical Reload Set
| Artifact | Why reload |
|---|---|
| `../README.md` | Dashboard and current gate |
| `../migration-status.md` | Visual progress status |
| `../resume.md` | Restart instructions |
| `task-checklist.md` | Package state and lost-function guard |

## Active Package
- Package: none
- Reason: not assigned

## Retired Context
| Context | Replacement artifact |
|---|---|

## Stale Artifacts
| Artifact/package | Reason | Replacement needed? |
|---|---|---|

## Pending Questions
| Question | Owner | Blocks |
|---|---|---|
""",
        root / "orchestration" / "completion-check.md": f"""# {feature} Completion Check

## Inputs Checked
| Artifact | Status |
|---|---|

## Checklist Status
| Package | Status | Verified? | Notes |
|---|---|---|---|

## Feature Coverage
| Feature point/surface | Implemented? | Verified? | Evidence |
|---|---|---|---|

## Approval And Divergence
| Decision | Approved? | Evidence |
|---|---|---|

## Verification Results
| Command/scenario | Result | Evidence |
|---|---|---|

## Legacy Dross Scan
| Finding | Decision | Evidence |
|---|---|---|

## Final Decision
- Complete? no
- Remaining gaps:
- Deferred items:
""",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create restart-safe migration workspace artifacts in the target repo."
    )
    parser.add_argument("--target", required=True, type=Path, help="Target repository root")
    parser.add_argument("--feature", required=True, help="Feature name or request")
    parser.add_argument("--source", help="Source repository path or URL")
    parser.add_argument("--design-doc", action="append", help="Design document path or URL")
    parser.add_argument("--slug", help="Override generated feature slug")
    parser.add_argument(
        "--workspace-root",
        default=".ai-migrations/feature-migrations",
        help="Workspace root relative to target, or an absolute path",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing template files. Default only creates missing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = args.target.resolve()
    slug = args.slug or slugify(args.feature)
    workspace_root = Path(args.workspace_root)
    root = workspace_root if workspace_root.is_absolute() else target / workspace_root
    root = root / slug

    for directory in [
        root,
        root / "source-exploration" / "feature-points",
        root / "orchestration" / "task-packages",
        root / "orchestration" / "subagent-reports",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    written = []
    skipped = []
    for path, content in build_templates(args, root, slug).items():
        if write_if_needed(path, content, args.force):
            written.append(path)
        else:
            skipped.append(path)

    print(f"workspace: {root}")
    print(f"written: {len(written)}")
    for path in written:
        print(f"  + {path.relative_to(root)}")
    if skipped:
        print(f"skipped_existing: {len(skipped)}")
        for path in skipped:
            print(f"  = {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
