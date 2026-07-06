# Subagent Coordination

Use this guide when a migration is too large for one active context. The goal is to keep the main agent as the orchestrator while subagents produce small, durable artifacts that can be reviewed, combined, and reloaded later.

## Contents

- Artifact Layout
- Visual Workspace Updates
- Resume Gate
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
.ai-migrations/feature-migrations/<feature-slug>/
  README.md
  migration-status.md
  artifact-index.md
  timeline.md
  resume.md
  orchestration/
    task-package-index.md
    task-checklist.md
    subagent-assignment-queue.md
    context-recovery.md
    completion-check.md
    task-packages/
      TP-###-<name>.md
    subagent-reports/
      TP-###-<name>.md
```

## Visual Workspace Updates

The migration workspace root is the visible control panel for the main agent, subagents, and humans. Initialize it before broad task splitting with:

```bash
python3 <skill-dir>/scripts/init_migration_workspace.py \
  --feature "<feature name>" \
  --source <source-root-or-url>
```

Run it from the target repository root, or add `--target <target-root>` when running from another directory.

After every package assignment, package result, split, stale decision, approval change, implementation slice, verification run, pause, or resume, the main agent should update:

- `README.md`: current gate, active package, next action, and quick links.
- `migration-status.md`: phase, surface, feature point, package, approval, and verification boards.
- `artifact-index.md`: artifact status and staleness.
- `timeline.md`: append-only event entry.
- `resume.md`: latest checkpoint, canonical reload set, blockers, and next action.

Subagents write package outputs and reports; the main agent reflects their results into the visual workspace.

## Resume Gate

When a migration resumes after interruption, context compression, a new chat, a tool crash, or visible context pressure, run this gate before any implementation edits:

1. Load only `resume.md`, `migration-status.md`, `artifact-index.md`, `orchestration/task-checklist.md`, `orchestration/subagent-assignment-queue.md`, and the active package named by the checklist.
2. Re-evaluate packages that are `ready`, `in-progress`, `stale`, `risky`, or frontend-related.
3. Split any package that is no longer one-pass-feasible.
4. Assign executable packages to subagents in `subagent-assignment-queue.md`.
5. Dispatch one bounded package at a time; after each report, update the queue, checklist, status board, timeline, and resume file.

Do not continue frontend implementation directly in the main agent after resume. The main agent owns orchestration, package splitting, report review, record updates, and final integration decisions. Frontend exploration, frontend implementation, frontend verification, broad implementation, and any package that previously caused context pressure must be assigned to a subagent.

If subagent tools are unavailable for mandatory-subagent work, mark the package `blocked-subagent-unavailable`, record the blocker in `subagent-assignment-queue.md` and `resume.md`, and ask for subagent capability instead of silently switching to main-agent serial execution.

### orchestration/subagent-assignment-queue.md

Keep this file as the dispatch queue.

Required sections:

```markdown
# <Feature> Subagent Assignment Queue

## Resume Gate
- Last resume check:
- Subagent capability: available | unavailable | unknown
- Main-agent implementation allowed? no for frontend/broad/resumed work
- Current dispatch:

## Queue
| Package | Role | Surface | Mandatory subagent? | Allowed inputs | Write set | Status | Report path |
|---|---|---|---|---|---|---|---|

## Blocked Subagent Work
| Package | Reason | Needed capability | Next action |
|---|---|---|---|

## Dispatch Log
| Time | Package | Agent/role | Result | Report |
|---|---|---|---|---|
```

## When To Split

Create task packages when any of these are true:

- The source feature has multiple entry points, workflows, jobs, events, or UI paths.
- The candidate source files or call chain are too large to keep in memory.
- The target implementation crosses multiple owners such as API, domain, persistence, UI, jobs, or integrations.
- The source and target differ by language, framework, runtime, or architecture, such as Java service code migrating to Airflow.
- The feature has both frontend and backend/API surfaces that need separate owners, tests, and approval.
- Frontend discovery would require reading broad route/page/component/store/API trees before producing an artifact.
- Work is being resumed after interruption and the package is frontend, implementation, verification, broad, or previously context-heavy.
- Source exploration finds full paths, source package prefixes, hard-coded endpoints, generated paths, or other source-specific implementation tokens.
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
- Keep the workspace dashboard, status, artifact index, timeline, and resume file current enough that a restarted agent can continue without chat history.
- After resume, use `subagent-assignment-queue.md` as the execution source of truth. Do not self-assign mandatory-subagent packages to `main-agent`.

## Task Sizing And Checklist

Before executing any package, classify one-pass feasibility:

- `yes`: scope, inputs, dependencies, permissions, and write set are small enough to complete in one pass.
- `no-needs-split`: split the package before execution.
- `blocked`: required approval, input, tool, permission, or dependency is missing.
- `risky`: can start only if the package has narrow stop conditions and a rollback or handoff plan.

After resume, any `risky` frontend or implementation package should normally become `no-needs-split` or be assigned to a subagent with tight stop conditions. Do not let it become a long main-agent coding session.

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

Mirror the checklist summary into `migration-status.md` and append the material event to `timeline.md`.

Mirror dispatch status into `subagent-assignment-queue.md`; completion is blocked while a mandatory-subagent package is owned by `main-agent`.

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
| `frontend-route-indexer` | Thin route/menu/feature-flag/auth/i18n index before deep frontend reads | `source-exploration/frontend/frontend-surface-index.md`, candidate micro-packages |
| `frontend-page-explorer` | One page or route container and direct imports only | page/container feature point, direct files, visible behavior |
| `frontend-component-explorer` | One component cluster with bounded children | component feature point, props/events/slots, visible states |
| `frontend-state-api-explorer` | One store/query/mutation/API-client/generated-type path | state/API feature point, parameter and response mapping |
| `frontend-form-validation-explorer` | One form, validation path, submit path, or visible message set | form/validation feature point |
| `frontend-visible-state-explorer` | Loading, empty, error, permission, disabled, accessibility, i18n, analytics, or telemetry behavior | visible-state feature point |
| `backend-surface-explorer` | API contracts, handlers, domain services, persistence, jobs/events, integrations, authorization, validation, transactions, idempotency | backend/API feature-point files, evidence IDs, report |
| `config-center-explorer` | Nacos, Apollo, Spring Cloud Config, Consul, etcd, Vault, ConfigMap/Secret, feature flag, platform config, env injection | `source-exploration/config/config-center-inventory.md`, blockers, owners, verification plan |
| `target-paradigm-mapper` | Cross-language/cross-framework/runtime changes, especially Java-to-Airflow or service-to-DAG migration | `target-paradigm-map.md`, target primitives, source-shape rejection decisions |
| `coverage-matrix-verifier` | Many parameters, branches, side effects, config, schedules, runtime controls, or previous coverage misses | `source-exploration/coverage/feature-coverage-matrix.md`, gaps, blockers, verification plan |
| `design-intent-extractor` | Large or ambiguous design documents | target intent, acceptance criteria, explicit changes, questions |
| `legacy-smell-auditor` | Smell and dross classification after feature points exist | `legacy-smells.md` updates and severe-fix recommendations |
| `legacy-dross-auditor` | Full paths, source package prefixes, file URLs, old domains, generated paths, and source-specific tokens that may have been copied | `legacy-dross-scan.md`, firewall decisions, fixes or required approvals |
| `target-architecture-mapper` | Target analogs, owners, boundaries, patterns, and tests | target mapping artifact and report |
| `reconciliation-designer` | Combining reduced artifacts into decisions | baseline-vs-target matrix, design draft updates |
| `implementation-slice-agent` | One approved implementation slice, preferably one surface at a time | patch in disjoint write set, tests, report |
| `verification-agent` | Independent verification of behavior, approval, and coverage | verification results and gaps |

## Delegation Rules

- Give each subagent only the package file and the minimal referenced artifacts.
- Do not ask one subagent to ingest the complete source, complete target, and complete design corpus unless the package explicitly justifies it.
- Do not ask a frontend subagent to understand the whole frontend project. Require a `frontend-route-indexer` or existing `frontend-surface-index.md` before page/component/state/API exploration.
- Split frontend work by route, page/container, component cluster, state/API path, form/validation path, visible states, and tests when any one package would read broad directories or more than a small direct file set.
- Assign a `target-paradigm-mapper` before implementation when source and target language, framework, runtime, or architecture differ. Do not let implementation packages decide the target shape from source code.
- Assign a `coverage-matrix-verifier` before implementation and before completion when parameters, branches, side effects, or runtime controls are numerous or were previously missed.
- Assign third-party config center discovery to a bounded `config-center-explorer` package when config usage is present or unknown. Do not hide missing external config inside backend implementation notes.
- After resume, assign frontend exploration, frontend implementation, frontend verification, and broad implementation packages to subagents. Main-agent ownership is allowed only for orchestration and tiny non-frontend mechanical edits.
- Do not assign a package marked `no-needs-split` or `blocked`; split it or unblock it first.
- For code-edit packages, assign a disjoint write set and remind the subagent not to revert unrelated changes.
- Split frontend and backend implementation into separate packages when both surfaces exist, then add a coordination or verification package for the end-to-end workflow.
- For frontend implementation, prefer separate packages for route wiring, page/container orchestration, component rendering, form validation, state/API integration, visible states, and tests.
- Run or delegate a legacy dross audit before completion when source-specific tokens are known or the target patch contains suspicious paths.
- Exploration and design packages may write artifacts before design approval. Implementation packages may start only after approved slices are recorded.
- Subagents may recommend behavior changes, smell remediation, or drops, but the main agent owns reconciliation and approval gates.
- If a package discovers evidence that changes design scope, mark dependent packages `stale`, update `context-recovery.md`, and return to design approval before implementation continues.
- After a subagent report is accepted, update `artifact-index.md`, `migration-status.md`, `timeline.md`, and `resume.md` before assigning the next package.
- If the main agent starts editing a mandatory-subagent package directly, stop, record the process defect, retire the partial context into a package note, and re-dispatch the package or a smaller replacement package.

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

Also keep the root `resume.md` in sync with `context-recovery.md`. A restarted agent should read `resume.md` first, then open only the artifacts named by the current package.

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

The final decision can be `yes` only when every required checklist item is `verified` or explicitly `deferred` with approval or a recorded reason. It must be `no` when mandatory-subagent work was performed only by the main agent after resume without a recorded exception.
