# Subagent Coordination

Use this guide when a migration is too large for one active context. The goal is to keep the main agent as the orchestrator while subagents produce small, durable artifacts that can be reviewed, combined, and reloaded later.

## Contents

- Artifact Layout
- When To Split
- Main-Agent Responsibilities
- Task Sizing And Checklist
- Package Template
- Subagent Report Template
- Recommended Roles
- Delegation Rules
- Context Recovery
- Completion Check

## Artifact Layout

Use the target repository's existing agent artifact convention when one exists. Otherwise write:

```text
.ai-migrations/feature-migrations/<feature-slug>/orchestration/
  task-package-index.md
  task-checklist.md
  context-recovery.md
  completion-check.md
  task-packages/
    TP-###-<name>.md
  subagent-reports/
    TP-###-<name>.md
```

## When To Split

Create task packages when any of these are true:

- The source feature has multiple entry points, workflows, jobs, events, or UI paths.
- The candidate source files or call chain are too large to keep in memory.
- The target implementation crosses multiple owners such as API, domain, persistence, UI, jobs, or integrations.
- The feature has both frontend and backend/API surfaces that need separate owners, tests, and approval.
- Design documents are large, contradictory, or contain multiple alternatives.
- Implementation can be split into disjoint approved slices.
- Verification needs independent coverage of compatibility, security, data, or integration behavior.

For small migrations, a single agent may execute the same package protocol serially.

## Main-Agent Responsibilities

- Own user-facing decisions, approvals, final design, final integration, and final report.
- Prepare task packages with narrow inputs and explicit stop conditions.
- Assess whether each package can be completed in one pass before assignment or execution.
- Maintain `task-checklist.md` as the source of truth for package state and final check status.
- Keep active context limited to the request, task-package index, feature-point index, migration design, migration record, and current package.
- Merge only persisted artifacts, evidence IDs, and concise reports.
- Retire raw context after artifacts are written.
- Mark stale packages when design, source evidence, or target ownership changes.

## Task Sizing And Checklist

Before executing any package, classify one-pass feasibility:

- `yes`: scope, inputs, dependencies, permissions, and write set are small enough to complete in one pass.
- `no-needs-split`: split the package before execution.
- `blocked`: required approval, input, tool, permission, or dependency is missing.
- `risky`: can start only if the package has narrow stop conditions and a rollback or handoff plan.

Maintain `task-checklist.md` with:

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

Update the checklist after every package result, approval change, split, stale decision, implementation slice, verification run, or context handoff.

## Package Template

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

## Subagent Report Template

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

## Recommended Roles

| Role | Use for | Must output |
|---|---|---|
| `source-entrypoint-explorer` | One legacy entry point, workflow, domain slice, job, event, or UI path | `feature-points/<slug>.md`, evidence IDs, report |
| `frontend-surface-explorer` | UI routes, pages, components, forms, client state, API clients, generated types, visible validation, permissions display, analytics, accessibility | frontend feature-point files, evidence IDs, report |
| `backend-surface-explorer` | API contracts, handlers, domain services, persistence, jobs/events, integrations, authorization, validation, transactions, idempotency | backend/API feature-point files, evidence IDs, report |
| `design-intent-extractor` | Large or ambiguous design documents | target intent, acceptance criteria, explicit changes, questions |
| `legacy-smell-auditor` | Smell and dross classification after feature points exist | `legacy-smells.md` updates and severe-fix recommendations |
| `target-architecture-mapper` | Target analogs, owners, boundaries, patterns, and tests | target mapping artifact and report |
| `reconciliation-designer` | Combining reduced artifacts into decisions | baseline-vs-target matrix, design draft updates |
| `implementation-slice-agent` | One approved implementation slice, preferably one surface at a time | patch in disjoint write set, tests, report |
| `verification-agent` | Independent verification of behavior, approval, and coverage | verification results and gaps |

## Delegation Rules

- Give each subagent only the package file and the minimal referenced artifacts.
- Do not ask one subagent to ingest the complete source, complete target, and complete design corpus unless the package explicitly justifies it.
- Do not assign a package marked `no-needs-split` or `blocked`; split it or unblock it first.
- For code-edit packages, assign a disjoint write set and remind the subagent not to revert unrelated changes.
- Split frontend and backend implementation into separate packages when both surfaces exist, then add a coordination or verification package for the end-to-end workflow.
- Exploration and design packages may write artifacts before design approval. Implementation packages may start only after approved slices are recorded.
- Subagents may recommend behavior changes, smell remediation, or drops, but the main agent owns reconciliation and approval gates.
- If a package discovers evidence that changes design scope, mark dependent packages `stale`, update `context-recovery.md`, and return to design approval before implementation continues.

## Context Recovery

Maintain `context-recovery.md` so work can resume without reloading the world:

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

The canonical reload set should usually be the task-package index, task checklist, feature-point index, migration design, design approval, migration record, current package, and any feature-point files named by the current package.

## Completion Check

Write `completion-check.md` before declaring the migration done:

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

## Final Decision
- Complete? yes/no
- Remaining gaps:
- Deferred items:
```

The final decision can be `yes` only when every required checklist item is `verified` or explicitly `deferred` with approval or a recorded reason.
