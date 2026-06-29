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

## Source Exploration Artifacts
| Artifact | Purpose | Status |
|---|---|---|

## Subagent Task Ledger
| Package ID | Role | Scope | Inputs | Outputs | Status | Decision impact |
|---|---|---|---|---|---|---|

## Feature Point Files
| Surface | Feature point | Markdown file | Used in design? | Notes |
|---|---|---|---|---|

## Surface Coverage
| Surface | Present? | Source evidence | Target owner | Implementation status | Verification |
|---|---|---|---|---|---|

## Design Approval
| Item | Status | Evidence |
|---|---|---|

## Essence And Dross Decisions
| Source item | Classification | Source evidence | Target decision | Verification |
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

## Implementation Slices
- [ ] Contract and schema
- [ ] Subagent task packages prepared
- [ ] Subagent package reports integrated
- [ ] Context recovery file current
- [ ] Feature point Markdown split
- [ ] Surface coverage recorded
- [ ] Migration design approved
- [ ] Frontend slice complete or documented not applicable
- [ ] Backend/API slice complete or documented not applicable
- [ ] End-to-end flow verified when frontend and backend both exist
- [ ] Design-doc behavior
- [ ] Legacy compatibility behavior
- [ ] Full migration coverage for aligned behavior
- [ ] Essence kept
- [ ] Dross rejected
- [ ] Simple legacy smell fixes
- [ ] Severe legacy issue remediation
- [ ] Domain behavior
- [ ] Persistence and integrations
- [ ] Entry-point wiring
- [ ] Rollout, flags, migration, or deprecation path
- [ ] Observability
- [ ] Tests and verification

## Verification
| Command/scenario | Expected | Result |
|---|---|---|
```

## Evidence Rules

- Use repository-relative file paths and line numbers where practical.
- Link each important contract claim to code, test, schema, config, history, or runtime evidence.
- Link source behavior claims to persisted source exploration artifacts where possible.
- Link delegated work to task-package files and subagent reports; do not cite unpersisted chat-only handoffs.
- Link frontend, backend/API, and end-to-end coverage to feature-point files, target files, and verification evidence.
- Link design decisions to feature point Markdown files and approval evidence.
- Link essence/dross decisions to source evidence, target decisions, and verification.
- Link legacy smell and severe issue decisions to source evidence and verification.
- Label uncertain claims as assumptions instead of presenting them as facts.
- Record intentional differences before or during implementation, not only after tests fail.
- Link every non-one-to-one behavior decision to a design document, user instruction, or explicit compatibility decision.
- Mark design/source divergences as unconfirmed until the current user request or another explicit approval confirms them.
- For aligned behavior, record how complete migration coverage was verified.
- Do not mark the migration complete when a present frontend or backend surface is unimplemented or unverified.
- Record the canonical reload set and stale package status before pausing or handing work off.
- Keep raw copied source code out of the record; cite it and summarize the behavior.
