# Migration Record Contract

Create one migration record per feature at:

`<target-root>/.codex/feature-migrations/<feature-slug>/migration-record.md`

Keep it concise but evidence-backed. Update it as discoveries invalidate earlier assumptions.

## Required Shape

```markdown
# <Feature> Migration Record

## Scope
- Source repository:
- Target repository:
- Requested behavior:
- Explicit non-goals:

## Recovered Contract
| Scenario | Input/trigger | Expected result | Errors/side effects | Source evidence |
|---|---|---|---|---|

## Source Implementation Trace
| Responsibility | Symbols/files | Callers/dependencies | Notes |
|---|---|---|---|

## Target Mapping
| Source responsibility | Target owner/pattern | Action | Verification |
|---|---|---|---|

## Intentional Differences
| Difference | Reason | Compatibility impact | Approval/evidence |
|---|---|---|---|

## Risks And Assumptions
| Item | Status | Mitigation or decision |
|---|---|---|

## Implementation Slices
- [ ] Contract and schema
- [ ] Domain behavior
- [ ] Persistence and integrations
- [ ] Entry-point wiring
- [ ] Observability
- [ ] Tests and verification

## Verification
| Command/scenario | Expected | Result |
|---|---|---|
```

## Evidence Rules

- Use repository-relative file paths and line numbers where practical.
- Link each important contract claim to code, test, schema, config, history, or runtime evidence.
- Label uncertain claims as assumptions instead of presenting them as facts.
- Record intentional differences before or during implementation, not only after tests fail.
- Keep raw copied source code out of the record; cite it and summarize the behavior.
