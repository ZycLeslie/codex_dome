---
name: migrate-feature-to-v2
description: Discover a named feature or business capability in a legacy source repository, recover its observable behavior and implementation evidence, then implement and verify an architecture-appropriate, AI-friendly 2.0 version in a target repository. Use when Codex needs to perform cross-repository feature migration, legacy-to-new-system modernization, 功能迁移, 特性迁移, 老仓功能探索, 旧系统升级到 2.0, or reconstruct a function from source code and deliver it end to end in a new codebase.
---

# Migrate Feature To V2

Recover the feature contract from the source repository, then reimplement that contract using the target repository's architecture. Treat source code as behavioral evidence, not as a template to paste.

## Inputs And Defaults

Resolve these inputs before editing:

- **Source repository**: legacy repository path or URL used as read-only evidence.
- **Target repository**: AI-friendly 2.0 repository where implementation belongs.
- **Feature request**: user-visible capability, business rule, API, workflow, job, UI behavior, or named function to migrate.
- **Acceptance criteria**: explicit requirements when provided; otherwise recover them from source behavior and tests.

Use the current workspace as the target repository when the user gives only a source repository. Treat a user-provided repository as the source unless they explicitly call it the 2.0 target. If both repository roles remain ambiguous and editing the wrong repository is plausible, ask one concise question before modifying code.

For remote URLs, clone or fetch only after obtaining any required approval. Do not modify or commit in the source repository unless the user explicitly requests it.

## Non-Negotiables

- Preserve externally observable business behavior unless the user requests a behavior change.
- Adapt the implementation to target conventions, ownership boundaries, frameworks, and existing abstractions.
- Do not blindly copy source files, legacy architecture, generated code, obsolete dependencies, or known defects.
- Trace security, authorization, validation, transactions, idempotency, persistence, events, and integrations explicitly.
- Keep the target repository buildable throughout the migration and protect unrelated user changes.
- Add tests that prove the recovered contract and requested 2.0 behavior.
- Make intentional behavior differences explicit in the migration record and final report.
- Interpret "AI-friendly" as discoverable, explicit, composable, testable, and observable. Do not add an LLM, agent endpoint, or weaken security merely to claim AI readiness.

## Workflow

### 1. Establish The Two-Repository Context

1. Resolve local source and target roots and confirm their roles.
2. Read repository instructions, manifests, architecture docs, and recent relevant changes in both repositories.
3. Inspect target worktree changes before editing. Never overwrite unrelated changes.
4. Profile both repositories when they are unfamiliar:

   `python3 <skill-dir>/scripts/profile_repositories.py --source <source-root> --target <target-root> --output-dir <target-root>/.codex/feature-migrations/<feature-slug>`

Use the profile as orientation only. Read actual source files before making decisions.

### 2. Recover The Source Feature Contract

Start from user-visible or externally callable entry points, then trace inward:

1. Search for route paths, command names, UI labels, event names, configuration keys, database entities, logs, tests, and likely symbols with `rg`.
2. Follow the call chain through controllers/handlers, orchestration, domain logic, persistence, integrations, and emitted side effects.
3. Inspect tests, fixtures, schemas, API specifications, migrations, and configuration that constrain behavior.
4. Use `git log`, `git blame`, and historical diffs when current intent is unclear.
5. Record file-and-line evidence for each important behavior.

Recover at least:

- inputs, outputs, defaults, and error semantics
- permissions, validation, and security constraints
- state transitions, transactions, and idempotency
- persistence reads/writes and data shape
- synchronous and asynchronous side effects
- integration contracts, timeouts, retries, and fallback behavior
- configuration, flags, limits, and compatibility expectations
- observable logs, metrics, traces, and audit events

Separate **essential behavior** from **legacy implementation accidents**. Do not preserve incidental class layouts, duplicated logic, or framework workarounds unless they are required for compatibility.

### 3. Map The Contract Onto The Target Architecture

Explore the target before designing:

1. Find the closest analogous feature and identify its entry-point, domain, persistence, integration, test, and observability patterns.
2. Reuse target-owned abstractions when they genuinely match the recovered responsibility.
3. Build a responsibility map: source responsibility, source evidence, target owner, implementation action, and verification.
4. Identify compatibility gaps in data models, APIs, event schemas, dependencies, or operational assumptions.
5. Prefer a thin adapter at a real boundary over spreading legacy assumptions through target code.

Do not create a parallel architecture just because the source repository used one.

### 4. Write A Migration Record

Before substantial edits, create or update:

`<target-root>/.codex/feature-migrations/<feature-slug>/migration-record.md`

Include the feature contract, source evidence, target mapping, intentional differences, risk decisions, implementation slices, and verification plan. Use `references/migration-record-contract.md` for the required shape.

Proceed autonomously when evidence supports a safe implementation. Pause only when an unresolved ambiguity could materially change business behavior, security, data integrity, or the public contract.

### 5. Implement A Complete Vertical Slice

Implement the smallest complete slice that delivers the feature through its real entry point:

1. Add or update explicit contracts and schemas.
2. Implement domain behavior in the target's existing ownership boundaries.
3. Wire persistence, integrations, configuration, dependency injection, routes, handlers, jobs, or UI as required.
4. Preserve authorization, validation, transactional behavior, idempotency, and failure semantics.
5. Add logs, metrics, traces, or audit events consistent with target conventions.
6. Remove temporary duplication or compatibility scaffolding that is not needed after the slice works.

For detailed 2.0 design guidance, read `references/ai-friendly-v2.md` when choosing between multiple viable target designs.

### 6. Verify Behavior And Integration

Derive verification scenarios from the recovered contract, not merely from copied source tests.

- Add focused unit tests for business rules and edge cases.
- Add integration or contract tests for boundaries changed by the migration.
- Use differential, golden, or fixture-based comparison against the source when both versions can run deterministically.
- Run target formatting, static checks, build, and relevant tests; broaden checks when shared behavior changed.
- Search for missing registrations, routes, dependency injection wiring, schemas, migrations, flags, and documentation.
- Verify failure paths, authorization, idempotency, and side effects, not only the happy path.

If the source behavior cannot be executed, state which claims are proven by static evidence and which remain assumptions.

### 7. Report The Result

Report:

- source entry points and strongest implementation evidence
- target files and architecture owners changed
- preserved behaviors and intentional differences
- verification commands and outcomes
- remaining assumptions, risks, and follow-up work

Do not declare the migration complete while required target wiring, tests, or verification remain unfinished.

## Decision Rules

- When source behavior conflicts with target conventions, preserve the business contract and express it through target conventions.
- When source behavior conflicts with explicit user requirements, follow the user requirement and document the intentional difference.
- When a target abstraction almost fits but would distort the contract, add a narrow adapter or extend the abstraction with tests.
- When evidence is contradictory, prefer externally observable behavior and executable tests over comments or names.
- When the source contains an apparent defect, do not silently reproduce or silently fix it. Record the finding and choose based on compatibility requirements.
