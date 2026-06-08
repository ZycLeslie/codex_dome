---
name: migrate-feature-to-v2
description: Discover a named feature or business capability in a legacy source repository, recover its observable behavior and implementation evidence, reconcile it with 2.0 design documents or requested optimizations, then implement and verify an architecture-appropriate, AI-friendly target version. Use when an AI coding agent, automation workflow, or engineering team needs to perform cross-repository feature migration, non-one-to-one modernization, design-doc-driven implementation, 功能迁移, 特性迁移, 老仓功能探索, 旧系统升级到 2.0, 功能优化, 设计文档落地, or reconstruct a function from source code and deliver the intended 2.0 capability end to end in a new codebase.
---

# Migrate Feature To V2

Recover the legacy behavior from the source repository, reconcile it with the intended 2.0 design, then implement the target capability using the target repository's architecture. Treat source code as behavioral evidence, not as a template to paste; treat design documents as the intended future state, not optional commentary.

## Inputs And Defaults

Resolve these inputs before editing:

- **Source repository**: legacy repository path or URL used as read-only evidence.
- **Target repository**: AI-friendly 2.0 repository where implementation belongs.
- **Feature request**: user-visible capability, business rule, API, workflow, job, UI behavior, or named function to migrate.
- **Design documents**: optional PRD, technical design, API spec, OpenSpec change, ADR, issue, ticket, or acceptance document that defines the 2.0 target behavior.
- **Change intent**: whether the work is compatible migration, optimized behavior, redesigned workflow, API replacement, feature split/merge, deprecation, or greenfield implementation informed by legacy evidence.
- **Acceptance criteria**: explicit requirements when provided; otherwise recover them from source behavior and tests.

Use the current workspace as the target repository when the user gives only a source repository. Treat a user-provided repository as the source unless they explicitly call it the 2.0 target. If both repository roles remain ambiguous and editing the wrong repository is plausible, ask one concise question before modifying code.

For remote URLs, clone or fetch only after obtaining any required approval. Do not modify or commit in the source repository unless the user explicitly requests it.

## Non-Negotiables

- Preserve externally observable business behavior unless the user requests a behavior change.
- When design documents exist, implement the intended 2.0 behavior they specify while using the source repository to recover compatibility obligations and hidden business rules.
- When a design document or optimization request diverges from recovered source behavior, require explicit user confirmation unless the current task already clearly authorizes that exact divergence.
- When design documents and recovered source behavior are consistent, perform a complete migration of the feature, including edge cases, validations, permissions, persistence, side effects, configuration, observability, and tests.
- Do not assume a one-to-one migration. Explicitly decide whether each legacy behavior is preserved, changed, replaced, deprecated, split, merged, or dropped.
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
2. Locate and read user-provided design documents or discover likely design artifacts in the target repo when the request references them.
3. Read repository instructions, manifests, architecture docs, and recent relevant changes in both repositories.
4. Inspect target worktree changes before editing. Never overwrite unrelated changes.
5. Profile both repositories when they are unfamiliar:

   `python3 <skill-dir>/scripts/profile_repositories.py --source <source-root> --target <target-root> --output-dir <target-root>/.ai-migrations/feature-migrations/<feature-slug>`

Use the profile as orientation only. Read actual source files before making decisions.

### 2. Interpret The 2.0 Design Intent

When design documents, tickets, OpenSpec changes, API specs, or explicit optimization requirements exist, analyze them before designing code:

1. Extract target outcomes, personas/callers, workflows, public contracts, data changes, non-functional requirements, rollout constraints, and acceptance criteria.
2. Identify explicit changes from legacy behavior: additions, removals, renamed concepts, stricter validation, relaxed validation, async conversion, permission changes, observability changes, data model changes, and compatibility windows.
3. Classify the migration mode:
   - `compatible migration`: preserve behavior while moving implementation.
   - `compatible enhancement`: keep old contract and add new behavior.
   - `behavior replacement`: old behavior is intentionally changed.
   - `workflow redesign`: source feature maps to a different target flow.
   - `split or merge`: one legacy feature becomes several target capabilities, or several legacy features become one target capability.
   - `deprecation`: old behavior remains only through adapters, warnings, or a sunset path.
   - `greenfield with legacy reference`: source is evidence, not the implementation blueprint.
4. Record unclear design requirements as questions only when a reasonable implementation would risk business behavior, security, data integrity, or public compatibility.

For detailed design-doc reconciliation guidance, read `references/design-driven-modernization.md`.

### 3. Recover The Source Baseline

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

### 4. Reconcile Legacy Behavior With The Target Design

Build a baseline-vs-target matrix before implementation:

- legacy scenario or behavior
- source evidence
- design requirement or requested optimization
- alignment status: aligned, source-only, design-only, or divergent
- decision: preserve, enhance, replace, split, merge, deprecate, or drop
- confirmation status for every divergent or dropping decision
- compatibility impact
- tests or acceptance checks

Use this matrix to prevent both common failures: blindly cloning legacy behavior when 2.0 intentionally changes it, and losing hidden business rules because the design document omits legacy edge cases.

Apply the confirmation gate:

- **Aligned**: source evidence and design document agree. Implement the full recovered behavior, not only the happy path.
- **Source-only**: source has behavior the design omits. Preserve it unless the omission is confirmed as intentional.
- **Design-only**: design adds behavior with no source equivalent. Implement it as new 2.0 behavior and verify it with design-derived tests.
- **Divergent**: design changes or contradicts source behavior. Pause and ask for confirmation before implementing the changed behavior, unless the user's current request explicitly approves the specific change.
- **Drop/deprecate**: any removal, replacement, or compatibility break requires explicit confirmation or documented approval.

### 5. Map The Target Capability Onto The Target Architecture

Explore the target before designing:

1. Find the closest analogous feature and identify its entry-point, domain, persistence, integration, test, and observability patterns.
2. Reuse target-owned abstractions when they genuinely match the intended 2.0 responsibility.
3. Build a responsibility map: source responsibility, design requirement, target owner, implementation action, and verification.
4. Identify compatibility gaps in data models, APIs, event schemas, dependencies, or operational assumptions.
5. Prefer a thin adapter at a real boundary over spreading legacy assumptions through target code.

Do not create a parallel architecture just because the source repository used one.

### 6. Write A Migration And Design Record

Before substantial edits, create or update a migration record. Use the target repository's existing agent/workflow artifact convention when one exists; otherwise default to:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-record.md`

Include the legacy baseline, design inputs, baseline-vs-target matrix, target mapping, intentional differences, risk decisions, implementation slices, and verification plan. Use `references/migration-record-contract.md` for the required shape.

Proceed autonomously when evidence supports a safe implementation. Pause only when an unresolved ambiguity could materially change business behavior, security, data integrity, or the public contract.

### 7. Implement A Complete Vertical Slice

Implement the smallest complete slice that delivers the intended 2.0 capability through its real entry point:

1. Add or update explicit contracts and schemas.
2. Implement domain behavior in the target's existing ownership boundaries according to the design decision matrix.
3. Wire persistence, integrations, configuration, dependency injection, routes, handlers, jobs, or UI as required.
4. Preserve or intentionally revise authorization, validation, transactional behavior, idempotency, and failure semantics according to the design record.
5. Add logs, metrics, traces, or audit events consistent with target conventions.
6. Remove temporary duplication or compatibility scaffolding that is not needed after the slice works.

For detailed 2.0 design guidance, read `references/ai-friendly-v2.md` when choosing between multiple viable target designs.

### 8. Verify Behavior, Design, And Integration

Derive verification scenarios from both the target design and the recovered source baseline, not merely from copied source tests.

- Add focused unit tests for business rules and edge cases.
- Add integration or contract tests for boundaries changed by the migration.
- Use differential, golden, or fixture-based comparison against the source for preserved behavior, and explicit new expectations for redesigned behavior.
- Run target formatting, static checks, build, and relevant tests; broaden checks when shared behavior changed.
- Search for missing registrations, routes, dependency injection wiring, schemas, migrations, flags, and documentation.
- Verify failure paths, authorization, idempotency, and side effects, not only the happy path.
- Verify compatibility adapters, deprecation paths, data migrations, rollout flags, and backfill behavior when the 2.0 design changes external contracts.
- For aligned behavior, verify complete migration coverage against the source baseline: all entry points, edge cases, validation failures, permissions, data mutations, emitted events, external calls, config-controlled behavior, logs, metrics, and audit output that matter externally.

If the source behavior cannot be executed, state which claims are proven by static evidence and which remain assumptions.

### 9. Report The Result

Report:

- design documents or optimization requirements used
- source entry points and strongest implementation evidence
- target files and architecture owners changed
- preserved behaviors, optimized behaviors, deprecated behaviors, and intentional differences
- verification commands and outcomes
- remaining assumptions, risks, and follow-up work

Do not declare the migration complete while required target wiring, tests, or verification remain unfinished.

## Decision Rules

- When source behavior conflicts with target conventions, preserve the business contract and express it through target conventions.
- When source behavior conflicts with explicit user requirements or design documents, follow the target requirement for the intended scope and document the compatibility impact.
- Do not treat a design/source conflict as approved just because it appears in a document. Ask for confirmation unless the current user request explicitly authorizes that specific behavior change.
- When a design document is vague, use the source baseline to fill business-rule gaps but do not invent 2.0 changes beyond the documented intent.
- When a design document is older than current target code or conflicts with target architecture, verify the current code path before implementing the document literally.
- When source behavior and design intent agree, migrate the complete feature contract before calling the work done.
- When a target abstraction almost fits but would distort the contract, add a narrow adapter or extend the abstraction with tests.
- When evidence is contradictory, prefer externally observable behavior and executable tests over comments or names.
- When the source contains an apparent defect, do not silently reproduce or silently fix it. Record the finding and choose based on compatibility requirements.
