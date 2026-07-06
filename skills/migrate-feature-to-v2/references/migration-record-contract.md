# Migration Record Contract

Create one migration record per feature at:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-record.md`

If the target repository already has an established location for agent, migration, or design artifacts, use that convention instead of this default.

Keep it concise but evidence-backed. Update it as discoveries invalidate earlier assumptions.

## Contents

- Required Shape
- Evidence Rules

## Required Shape

```markdown
# <Feature> Migration Record

## Scope
- Source repository:
- Target repository:
- Design documents:
- Requested behavior:
- Migration mode:
- Repository access method:
- Explicit non-goals:

## Visual Workspace
| Artifact | Purpose | Current status | Last updated |
|---|---|---|---|
| `README.md` | Dashboard and quick links |  |  |
| `migration-status.md` | Phase, surface, package, approval, and verification boards |  |  |
| `artifact-index.md` | Artifact inventory and staleness |  |  |
| `timeline.md` | Append-only event log |  |  |
| `resume.md` | Restart checkpoint and canonical reload set |  |  |

## Source Exploration Artifacts
| Artifact | Purpose | Status |
|---|---|---|

## Subagent Task Ledger
| Package ID | Role | Scope | One-pass feasibility | Inputs | Outputs | Status | Decision impact |
|---|---|---|---|---|---|---|---|

## Subagent Assignment Queue
| Package | Role | Runner | Mandatory subagent? | Owner/job ID | Status | Report path |
|---|---|---|---|---|---|---|

## Multica Jobs
| Package | Role | Multica job ID | Status | Report path | Merge decision |
|---|---|---|---|---|---|

## Task Checklist
| Package | Surface | Objective | Status | Verification | Final check |
|---|---|---|---|---|---|

## Feature Point Files
| Surface | Feature point | Markdown file | Used in design? | Notes |
|---|---|---|---|---|

## Surface Coverage
| Surface | Present? | Source evidence | Target owner | Implementation status | Verification |
|---|---|---|---|---|---|

## Feature Coverage Matrix
| Coverage item | Source evidence | Target mapping | Status | Verification | Gap |
|---|---|---|---|---|---|

## Target Paradigm Mapping
| Source language/framework/runtime | Target language/framework/runtime | Migration mode | Map artifact | Status |
|---|---|---|---|---|

## Source Shape Rejection
| Source shape/token | Target-native replacement | Approved if preserved? | Verification |
|---|---|---|---|

## Config Center Inventory
| Key | Provider | Namespace/group/app | Profile/env | Target mapping | Required? | Sensitive? | Owner | Status | Verification |
|---|---|---|---|---|---|---|---|---|---|

## Missing Or Blocked Config
| Config | Why needed | Blocks | Owner | Decision |
|---|---|---|---|---|

## Design Approval
| Item | Status | Evidence |
|---|---|---|

## Essence And Dross Decisions
| Source item | Classification | Source evidence | Target decision | Verification |
|---|---|---|---|---|

## Legacy Dross Firewall
| Source token/path/prefix | Type | Target replacement or compatibility decision | Scan result | Verification |
|---|---|---|---|---|

## Legacy Smell Remediation
| Smell/problem | Severity | Source evidence | Target decision | Verification |
|---|---|---|---|---|

## Design Intent
| Requirement | Source/design reference | Target behavior | Acceptance check |
|---|---|---|---|

## Recovered Legacy Baseline
| Scenario | Input/trigger | Expected result | Errors/side effects | Source evidence |
|---|---|---|---|---|

## Baseline Vs Target Matrix
| Legacy behavior | Source evidence | 2.0 design requirement | Alignment | Decision | Confirmation | Compatibility impact | Verification |
|---|---|---|---|---|---|---|---|

## Divergence Confirmation
| Difference | Requires confirmation? | Confirmation source | Decision |
|---|---|---|---|

## Source Implementation Trace
| Responsibility | Symbols/files | Callers/dependencies | Notes |
|---|---|---|---|

## Target Mapping
| Source/design responsibility | Surface | Target owner/pattern | Action | Verification |
|---|---|---|---|---|

## Intentional Differences
| Difference | Reason | Compatibility impact | Approval/evidence |
|---|---|---|---|

## Risks And Assumptions
| Item | Status | Mitigation or decision |
|---|---|---|

## Context Recovery Ledger
| Item | Artifact or context | Status | Notes |
|---|---|---|---|

## Completion Check
| Item | Status | Evidence |
|---|---|---|

## Implementation Slices
- [ ] Contract and schema
- [ ] Visual workspace initialized and current
- [ ] Subagent task packages prepared
- [ ] Subagent assignment queue current after resume
- [ ] Multica job ledger current when multica is used
- [ ] One-pass feasibility assessed for every package
- [ ] Oversized packages split before execution
- [ ] Task checklist current
- [ ] Subagent package reports integrated
- [ ] Context recovery file current
- [ ] Resume file current for restart after interruption
- [ ] Feature point Markdown split
- [ ] Surface coverage recorded
- [ ] Feature coverage matrix complete for entry points, parameters, defaults, validation, branches, errors, side effects, config, schedules, and runtime controls
- [ ] Source and target language/framework/runtime identified
- [ ] Target paradigm map complete when source and target differ
- [ ] Source-language or source-framework structure rejected or explicitly approved as compatibility
- [ ] Third-party config center inventory complete or documented not applicable
- [ ] Required target config mapped, provisioned, or blocked with owner
- [ ] Migration design approved
- [ ] Frontend thin surface index written when frontend is present or unknown
- [ ] Frontend route/page/component/state/API/form/visible-state tasks split when applicable
- [ ] Frontend/resumed/broad implementation packages executed by subagents or blocked with reason
- [ ] Frontend slice complete or documented not applicable
- [ ] Backend/API slice complete or documented not applicable
- [ ] End-to-end flow verified when frontend and backend both exist
- [ ] Design-doc behavior
- [ ] Legacy compatibility behavior
- [ ] Full migration coverage for aligned behavior
- [ ] Essence kept
- [ ] Dross rejected
- [ ] Legacy full paths and source-specific tokens replaced or approved
- [ ] Legacy dross scan reviewed
- [ ] Simple legacy smell fixes
- [ ] Severe legacy issue remediation
- [ ] Domain behavior
- [ ] Persistence and integrations
- [ ] Entry-point wiring
- [ ] Rollout, flags, migration, or deprecation path
- [ ] Config center keys, profiles, feature flags, secrets, and dynamic refresh behavior verified
- [ ] Observability
- [ ] Tests and verification
- [ ] Coverage matrix rechecked after implementation
- [ ] Target paradigm map rechecked against final patch
- [ ] Completion check passed or gaps recorded

## Verification
| Command/scenario | Expected | Result |
|---|---|---|
```

## Evidence Rules

- Use repository-relative file paths and line numbers where practical.
- Link each important contract claim to code, test, schema, config, history, or runtime evidence.
- Link source behavior claims to persisted source exploration artifacts where possible.
- Link the current migration state to the root visual workspace files, especially `migration-status.md`, `artifact-index.md`, `timeline.md`, and `resume.md`.
- Link delegated work to task-package files and subagent reports; do not cite unpersisted chat-only handoffs.
- Link multica job IDs to package files, approved write sets, reports, and merge decisions when multica is used.
- Link task status to `task-checklist.md` and final decision to `completion-check.md`.
- Link frontend, backend/API, and end-to-end coverage to feature-point files, target files, and verification evidence.
- Link coverage matrix rows to source evidence, target mapping, and verification; do not rely on generic "covered by implementation" claims.
- Link cross-language/cross-framework decisions to `target-paradigm-map.md` and prove source-language structure was not copied without approval.
- Link config center entries to source evidence, target mappings, owners, and verification; do not expose secret values.
- Link design decisions to feature point Markdown files and approval evidence.
- Link essence/dross decisions to source evidence, target decisions, and verification.
- Link every legacy dross scan finding to a fix, approved compatibility decision, or deferred record.
- Link legacy smell and severe issue decisions to source evidence and verification.
- Label uncertain claims as assumptions instead of presenting them as facts.
- Record intentional differences before or during implementation, not only after tests fail.
- Link every non-one-to-one behavior decision to a design document, user instruction, or explicit compatibility decision.
- Mark design/source divergences as unconfirmed until the current user request or another explicit approval confirms them.
- For aligned behavior, record how complete migration coverage was verified.
- Do not mark the migration complete when a present frontend or backend surface is unimplemented or unverified.
- Do not mark the migration complete while any multica job is running, missing a report, stale, outside its write set, or inconsistent with the checklist.
- Do not mark the migration complete while required coverage matrix rows are blank, unknown, unmapped, or unverified.
- Do not mark cross-language/cross-framework migration complete while target code preserves source-language layers or framework scaffolding without explicit approval.
- Do not mark the migration complete while a required package is `ready`, `needs-split`, `blocked`, `in-progress`, or unverified.
- Do not mark the migration complete when mandatory-subagent frontend, resumed, or broad work was executed only by the main agent without a recorded exception.
- Do not mark the migration complete while required third-party config center entries are missing, unmapped, ownerless, or unverified.
- Do not mark the migration complete while legacy dross scan findings are unexplained.
- Record the canonical reload set and stale package status before pausing or handing work off.
- Keep `resume.md` and `orchestration/context-recovery.md` aligned before pausing, handing off, or responding after an interruption.
- Keep raw copied source code out of the record; cite it and summarize the behavior.
