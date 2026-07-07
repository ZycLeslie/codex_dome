# Source Docs First

Use this guide before broad source-code exploration. Existing source-repository specs and design artifacts are the first evidence layer for legacy intent. Code exploration verifies and fills gaps; it should not be the first expensive sweep when useful docs already exist.

## Required Artifact

Write or update:

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-docs-index.md
```

Required shape:

```markdown
# <Feature> Source Docs Index

## Summary
- Source docs present? yes | no | insufficient | stale
- Docs checked:
- Coverage:
- Exploration fallback needed? yes/no

## Candidate Docs
| Artifact | Type | Location | Version/date | Scope | Feature relevance | Trust level | Gaps |
|---|---|---|---|---|---|---|---|

## Source Contract Extract
| Requirement/behavior | Doc evidence | Applies to | Target use | Needs code verification? |
|---|---|---|---|---|

## Coverage Gaps
| Gap | Why docs are insufficient | Exploration package |
|---|---|---|

## Exploration Fallback Plan
| Package | Role | Scope | Runner | Output |
|---|---|---|---|---|
```

## What To Look For

Prefer high-signal source artifacts before reading large code areas:

- `docs/`, `design/`, `spec/`, `adr/`, `openapi/`, `swagger/`, `proto/`, `graphql/`
- README files, API contracts, PRD files, ADRs, runbooks, release notes, test plans, issue or ticket references
- `.md`, `.adoc`, `.rst`, `.yaml`, `.yml`, `.json`, `.proto`, `.graphql`, generated client contracts
- OpenSpec changes or similar source-repo capability specs

## Decision Rules

- Source docs describe legacy intent and public behavior; they are not automatic 2.0 target authority.
- If source docs are current and cover the feature contract, use them to seed the coverage matrix and then verify risky or ambiguous rows against code and tests.
- If source docs are stale, contradictory, or incomplete, label the trust level and list the missing behavior before opening code exploration.
- If no useful source docs exist, or docs cover less than the feature contract needed for migration, create 2-3 detailed exploration packages instead of one broad repository scan.
- Use `multica` first for those packages when available, otherwise use subagents.
- Each fallback package must have a bounded scope, allowed inputs, output artifact, and one-pass feasibility decision.

## Default Fallback Packages

When docs are absent or insufficient, start with two or three packages chosen from these dimensions:

| Package type | Use when | Output |
|---|---|---|
| Entry point and public contract | APIs, UI routes, commands, jobs, or events are known | feature-point files and coverage rows for entry points and parameters |
| Domain, data, and side effects | Business rules, persistence, external calls, transactions, or events are material | feature-point files for rules, data shape, integrations, and side effects |
| Frontend or runtime controls | UI behavior, config center, schedules, flags, observability, or tests are present or unknown | frontend/config/test artifacts and coverage gaps |

Do not proceed from source-doc indexing straight into implementation. The docs index must feed the migration design, coverage matrix, and any fallback exploration packages.
