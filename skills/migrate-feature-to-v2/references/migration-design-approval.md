# Migration Design Approval

Use this guide after source exploration is persisted and feature points are split into Markdown files. The goal is to move from discovery to implementation through an explicit, reviewable design gate.

## Contents

- Required Files
- migration-design.md
- design-approval.md
- Gate Rules

## Required Files

Use the target repository's existing artifact convention when one exists. Otherwise write:

```text
.ai-migrations/feature-migrations/<feature-slug>/migration-design.md
.ai-migrations/feature-migrations/<feature-slug>/design-approval.md
.ai-migrations/feature-migrations/<feature-slug>/target-paradigm-map.md when source and target paradigm differ
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/coverage/feature-coverage-matrix.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-packages/TP-###-<name>.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/completion-check.md
```

## migration-design.md

Required before implementation.

```markdown
# <Feature> Migration Design

## Scope
- Source repository:
- Target repository:
- Design documents:
- Feature point index:
- Non-goals:

## Feature Point Summary
| Surface | Feature point | Source markdown | Target decision | Notes |
|---|---|---|---|---|

## Surface Coverage
| Surface | Source evidence | Target owner | Decision | Verification |
|---|---|---|---|---|

## Feature Coverage Matrix
| Coverage area | Source rows | Target mapped? | Verification | Gap |
|---|---|---|---|---|

## Target Paradigm Mapping
| Source responsibility | Target primitive/artifact | Source shape rejected | Verification |
|---|---|---|---|

## Target Architecture
| Target owner/module | Surface | Responsibility | Source/design basis |
|---|---|---|---|

## Behavior Compatibility
| Behavior | Decision | Evidence | Verification |
|---|---|---|---|

## Intentional Differences
| Difference | Reason | Approval needed? | Compatibility impact |
|---|---|---|---|

## Essence, Dross, And Smells
| Item | Classification | Target action | Verification |
|---|---|---|---|

## Legacy Dross Firewall
| Source token/path/prefix | Classification | Target replacement | Compatibility approval needed? | Verification |
|---|---|---|---|---|

## Implementation Slices
| Slice | Surface | Files/modules | Depends on | Verification |
|---|---|---|---|---|

## Task Package Plan
| Package | Role | Slice/feature point | One-pass feasibility | Inputs | Allowed files/modules | Outputs | Verification | Status |
|---|---|---|---|---|---|---|---|---|

## Task Checklist Coverage
| Feature point/surface/slice | Covered by packages | One-pass feasible? | Gap |
|---|---|---|---|

## Full-Stack Coordination
| Flow | Frontend slice | Backend/API slice | Contract or integration check | E2E verification |
|---|---|---|---|---|

## Rollout And Operations
| Concern | Plan |
|---|---|

## Open Questions
| Question | Blocks implementation? | Proposed answer |
|---|---|---|

## Approval Request
- Requested approver:
- Approval scope:
- Approved slices:
- Approved task packages:
```

## design-approval.md

Required before implementation starts.

```markdown
# <Feature> Design Approval

## Approval Status
- Status: pending | approved | partially approved | rejected | changes requested
- Approver:
- Date/time:
- Approval source: conversation | ticket | PR | design review | other

## Approved Scope
| Surface/slice/package/decision | Approved? | Notes |
|---|---|---|

## Required Changes Before Implementation
| Change | Status |
|---|---|

## Implementation Gate
- Can implementation start? yes/no
- Reason:
```

## Gate Rules

- Do not edit target implementation code before approval is recorded.
- If approval is partial, implement only approved slices and task packages.
- If frontend and backend surfaces both exist, approval should identify which frontend slices, backend/API slices, and end-to-end checks are approved.
- Do not approve an implementation package that is `no-needs-split` or missing one-pass feasibility.
- Do not approve a design that copies legacy full paths, source package prefixes, file URLs, hard-coded endpoints, or environment-specific directories without an explicit compatibility reason and verification plan.
- Do not approve a cross-language or cross-framework design that lacks `target-paradigm-map.md` or recreates source-language layers without an approved external contract.
- Do not approve a design when required feature coverage matrix rows are blank, unknown, unmapped, or missing verification/defer approval.
- If a package is not approved, do not hand it to an implementation-slice agent.
- If design changes affect package inputs, mark the old package `stale`, update the package plan, and get approval for the changed package before implementation.
- If the implementation discovers a design-changing fact, update `migration-design.md` and get approval again before continuing.
- If the user explicitly says to proceed after reviewing the design in the current conversation, record that as approval evidence.
- Exploration artifacts, feature point Markdown files, and design documents may be created before approval.
