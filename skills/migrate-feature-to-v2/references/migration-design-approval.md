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
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-packages/TP-###-<name>.md
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

## Implementation Slices
| Slice | Surface | Files/modules | Depends on | Verification |
|---|---|---|---|---|

## Task Package Plan
| Package | Role | Slice/feature point | Inputs | Allowed files/modules | Outputs | Verification | Status |
|---|---|---|---|---|---|---|---|

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
- If a package is not approved, do not hand it to an implementation-slice agent.
- If design changes affect package inputs, mark the old package `stale`, update the package plan, and get approval for the changed package before implementation.
- If the implementation discovers a design-changing fact, update `migration-design.md` and get approval again before continuing.
- If the user explicitly says to proceed after reviewing the design in the current conversation, record that as approval evidence.
- Exploration artifacts, feature point Markdown files, and design documents may be created before approval.
