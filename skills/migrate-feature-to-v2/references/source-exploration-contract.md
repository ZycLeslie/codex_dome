# Source Exploration Contract

Persist source exploration results before implementing the target feature. The goal is traceability: another agent or engineer should be able to understand how the legacy behavior was recovered without redoing the whole search.

## Contents

- Default Location
- Required Artifacts
- CodeHub MCP Evidence Rules
- Quality Bar

## Default Location

Use the target repository's existing artifact convention when one exists. Otherwise write to:

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/
```

When task packages or subagents are used, write orchestration artifacts to the sibling directory:

```text
.ai-migrations/feature-migrations/<feature-slug>/orchestration/
```

## Required Artifacts

### orchestration/task-package-index.md

Required when the migration is broad enough to split across subagents or serial task packages. Use it as the work ledger so the main agent does not need to keep every exploration thread in active context.

Required sections:

```markdown
# <Feature> Task Package Index

## Overview
- Feature:
- Source:
- Target:
- Current active package:

## Packages
| Package ID | Role | Scope | One-pass feasibility | Inputs | Outputs | Status | Notes |
|---|---|---|---|---|---|---|---|

## Dependencies
| Package | Depends on | Reason |
|---|---|---|

## Approval Or Gate Status
| Package | Gate | Status | Evidence |
|---|---|---|---|
```

### orchestration/task-checklist.md

Required for every multi-package migration. Use it to prevent task loss across context compression, subagent handoffs, and partial approvals.

Required sections:

```markdown
# <Feature> Task Checklist

## Summary
- Feature:
- Current active package:
- Last updated:
- Completion check:

## Tasks
| Package | Surface | Objective | One-pass feasibility | Depends on | Status | Owner | Artifacts | Verification | Final check |
|---|---|---|---|---|---|---|---|---|---|

## Lost-Function Guard
| Feature point/surface | Covered by packages | Verified? | Gap |
|---|---|---|---|

## Deferred Or Blocked
| Task | Reason | Approval/evidence | Follow-up |
|---|---|---|---|
```

### orchestration/task-packages/TP-###-<name>.md

Required for every delegated or serial bounded task.

Required sections:

```markdown
# TP-### <Task Name>

## Objective
- Outcome:
- Role:
- Blocks:

## One-Pass Feasibility
- Feasibility: yes | no-needs-split | blocked | risky
- Reason:
- Required inputs ready? yes/no
- Required permissions/tools ready? yes/no
- Write set small and disjoint? yes/no/not applicable
- Split plan if not feasible:

## Allowed Inputs
| Input | Path or source | Purpose |
|---|---|---|

## Forbidden Inputs And Actions
- Do not read:
- Do not modify:
- Do not decide:

## Scope Boundaries
| In scope | Out of scope |
|---|---|

## Output Paths
| Artifact | Required content |
|---|---|

## Evidence Format
- Evidence IDs:
- Required file/line citations:
- Assumptions must be labeled: yes

## Stop Conditions
- Stop if:
- Ask main agent if:

## Acceptance Checks
| Check | Expected |
|---|---|

## Checklist Update
- Checklist row:
- Status to set when complete:
- Verification to record:

## Context Retirement Rule
- After this package completes, retain only:
- Retire:
```

### orchestration/subagent-reports/TP-###-<name>.md

Required after every subagent package or serial package completes. The report is the handoff artifact; do not depend on chat-only summaries.

Required sections:

```markdown
# TP-### <Task Name> Report

## Result
- Status: completed | blocked | partial | stale
- Summary:

## Artifacts Written
| Artifact | Purpose |
|---|---|

## Checklist Updates
| Package | Status | Verification | Notes |
|---|---|---|---|

## Evidence
| Claim | Evidence ID or location | Confidence |
|---|---|---|

## Decisions Or Recommendations
| Item | Recommendation | Requires approval? |
|---|---|---|

## Open Questions
| Question | Blocks next step? | Suggested owner |
|---|---|---|

## Context To Retire
- Raw files searched:
- Search logs:
- Long excerpts:
```

### orchestration/context-recovery.md

Required when task packages are used. Keep it current enough that another agent can resume without reloading broad source, target, and design context.

Required sections:

```markdown
# <Feature> Context Recovery

## Canonical Reload Set
| Artifact | Why reload |
|---|---|

## Active Package
- Package:
- Reason:

## Retired Context
| Context | Replacement artifact |
|---|---|

## Stale Artifacts
| Artifact/package | Reason | Replacement needed? |
|---|---|---|

## Pending Questions
| Question | Owner | Blocks |
|---|---|---|
```

### orchestration/completion-check.md

Required before declaring a migration complete. It should check task coverage, feature coverage, approvals, surfaces, and verification.

Required sections:

```markdown
# <Feature> Completion Check

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
- Complete? yes/no
- Remaining gaps:
- Deferred items:
```

### source-exploration.md

Human-readable summary of the source investigation.

Required sections:

```markdown
# <Feature> Source Exploration

## Source Access
- Repository:
- Access method: local checkout | generic git | CodeHub MCP | other
- Branch/ref/commit:
- Exploration timestamp:

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
```

### source-evidence.json

Machine-readable evidence index. Keep it compact and deterministic.

Recommended shape:

```json
{
  "feature": "<feature-slug>",
  "source": {
    "repository": "<path-or-url>",
    "accessMethod": "local checkout | generic git | CodeHub MCP | other",
    "ref": "<branch-or-commit>"
  },
  "evidence": [
    {
      "id": "EV-001",
      "claim": "Short behavior or implementation claim",
      "kind": "code | test | schema | config | history | codehub-mcp | runtime | docs | essence | dross | bad-smell",
      "location": "repo-relative/path:line or MCP resource identifier",
      "symbol": "optional symbol name",
      "notes": "brief explanation"
    }
  ]
}
```

### feature-point-index.md

Required navigation map for split feature point files. Use it to avoid carrying the full source exploration context in memory.

Required sections:

```markdown
# <Feature> Feature Point Index

## Overview
- Source:
- Ref:
- Feature:

## Feature Points
| ID | Surface | Feature point | Markdown file | Status | Notes |
|---|---|---|---|---|---|

## Design Inputs
| Topic | Surface | Feature point files | Design impact |
|---|---|---|---|

## Open Questions
| Question | Related feature points | Decision needed |
|---|---|---|
```

### feature-points/<feature-point-slug>.md

Required for every coherent feature point discovered during source exploration. Keep each file focused and small enough to load independently.

Required sections:

```markdown
# <Feature Point>

## Summary
- ID:
- Surface: frontend | backend-api | job-event | integration | data | config | observability | end-to-end
- Status:
- Owner/domain:

## Entry Points
| Entry point | Evidence |
|---|---|

## Surface Responsibilities
| Responsibility | Evidence | Notes |
|---|---|---|

## Behavior
| Scenario | Inputs/triggers | Expected result | Side effects | Evidence |
|---|---|---|---|---|

## Data And Integration
| Concern | Evidence | Notes |
|---|---|---|

## Essence And Dross
| Item | Classification | Evidence | Migration decision |
|---|---|---|---|

## Legacy Smells
| Smell/problem | Classification | Evidence | Target decision |
|---|---|---|---|

## Legacy Dross Firewall
| Token/path/prefix | Type | Target replacement | Scan token? |
|---|---|---|---|

## Target Design Hints
| Hint | Reason | Evidence |
|---|---|---|

## Open Questions
| Question | Why it matters | Needed before implementation? |
|---|---|---|
```

### legacy-smells.md

Required smell inventory. If no relevant smells are found, write `none found` with the evidence scope checked.

Required sections:

```markdown
# <Feature> Legacy Smells

## Summary
- Overall risk:
- Scope checked:

## Smell Inventory
| Smell/problem | Classification | Source evidence | Target decision | Verification |
|---|---|---|---|---|

## Implementation Detail Dross
| Token/path/prefix | Type | Source evidence | Target decision | Scan status |
|---|---|---|---|---|

## Deferred Items
| Item | Reason deferred | Risk | Follow-up |
|---|---|---|---|
```

### Supporting Artifacts

Create only when useful:

- `search-log.md`: high-signal searches and why they mattered.
- `candidate-files.txt`: files inspected or rejected.
- `call-trace.md`: entry point to domain/persistence/integration call chain.
- `legacy-dross-candidates.md`: full paths, source package prefixes, old endpoints, generated paths, and source-specific tokens that must not leak into target code.
- `codehub-mcp-evidence.md`: CodeHub MCP queries, resources, branch/ref details, and evidence IDs.

## CodeHub MCP Evidence Rules

When the source repository is a CodeHub URL or the user identifies it as CodeHub:

- Use the matching CodeHub MCP for source discovery.
- Record the MCP server/tool identity, repository identifier, branch/ref, and resource IDs or query parameters needed to reproduce the evidence.
- Do not replace CodeHub MCP evidence with generic Git, browser scraping, or raw HTTP unless the user explicitly approves a fallback.
- If CodeHub MCP is unavailable, stop before source exploration and ask the user to enable or install the correct MCP.

## Quality Bar

- Every recovered behavior in the migration record should point to at least one evidence item.
- Every broad migration should have task packages, package reports, and a context recovery file before implementation starts.
- Every task package should have a one-pass feasibility decision before execution.
- Every multi-package migration should maintain `task-checklist.md` and finish with `completion-check.md`.
- Tasks marked `no-needs-split` should be split before assignment or execution.
- Surface coverage should explicitly mark frontend, backend/API, jobs/events, integrations, data, config, observability, and end-to-end flow as present, absent, or unknown.
- If a frontend route, page, component, form, client API call, generated client, UI validation, visible permission state, or user workflow exists, it should have a frontend feature-point file and a verification plan.
- If no frontend exists, record the evidence for `not applicable` instead of silently skipping frontend work.
- Every meaningful feature point should have one focused Markdown file and an entry in `feature-point-index.md`.
- The migration design should cite feature point Markdown files rather than raw search output whenever possible.
- Main-agent decisions should cite persisted package reports or artifacts, not subagent private reasoning.
- Every important essence/dross decision should point to evidence and a migration decision.
- Every source-specific full path, package prefix, endpoint, generated path, or identifier found in the feature path should be classified as dross, compatibility, or needs-reconciliation.
- Legacy dross scan tokens should be recorded before implementation when source-specific strings are known.
- Every severe smell or defect discovered in the feature path should be recorded with a remediation or deferral decision.
- Label uncertain claims as assumptions.
- Prefer source tests, schemas, configs, and externally visible entry points over comments.
- Keep raw source excerpts short; cite locations instead of copying large blocks.
