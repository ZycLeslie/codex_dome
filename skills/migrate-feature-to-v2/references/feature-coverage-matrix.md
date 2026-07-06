# Feature Coverage Matrix

Use this guide to prevent missed feature points, especially when the source has many parameters, branches, side effects, or UI/API inputs.

## Required Artifact

Write:

```text
source-exploration/coverage/feature-coverage-matrix.md
```

Required sections:

```markdown
# <Feature> Feature Coverage Matrix

## Summary
- Coverage status: incomplete | complete | blocked
- Source artifacts checked:
- Target artifacts checked:
- Remaining gaps:

## Entry Points
| Entry point | Surface | Source evidence | Target artifact | Decision | Verification |
|---|---|---|---|---|---|

## Parameters And Fields
| Name | Surface | Type/format | Required/default | Validation/range | Source evidence | Target mapping | Verification |
|---|---|---|---|---|---|---|---|

## Branches And Errors
| Condition/error | Source behavior | Target behavior | Decision | Verification |
|---|---|---|---|---|

## Side Effects And State
| Effect/state change | Source evidence | Target mapping | Idempotency/transaction rule | Verification |
|---|---|---|---|---|

## Config, Schedule, And Runtime Controls
| Control | Source evidence | Target mapping | Owner | Verification |
|---|---|---|---|---|

## Coverage Gaps
| Gap | Risk | Blocks completion? | Owner | Next action |
|---|---|---|---|---|
```

## Discovery Sources

Build rows from all relevant sources, not only from implementation files:

- API specs, controller signatures, request/response DTOs, schemas, forms, generated clients
- tests, fixtures, migrations, config files, feature flags, scheduler definitions
- database columns, message schemas, event payloads, logs, metrics, audit records
- UI fields, validation messages, loading/empty/error states, permission display

## Rules

- Every required parameter, default, validation rule, branch, error, side effect, and runtime control needs a target mapping or an explicit approved defer/drop decision.
- Do not mark completion while any row is blank, `unknown`, `todo`, unverified, or blocked.
- When the target framework collapses multiple source steps into one primitive, keep one row per source behavior and point each row to the same target artifact.
- For high-parameter features, assign a `coverage-matrix-verifier` package before implementation and again before completion.
