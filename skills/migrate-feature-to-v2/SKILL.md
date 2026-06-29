---
name: migrate-feature-to-v2
description: Discover a named feature or business capability in a legacy source repository, split large migrations into bounded subagent task packages, persist source exploration evidence to disk, split recovered feature points into focused Markdown files, recover observable behavior, extract the valuable business essence, reject legacy dross and code smells, reconcile everything with 2.0 design documents or requested optimizations, produce an approvable migration design, then implement only after approval. Use when an AI coding agent, automation workflow, or engineering team needs to perform cross-repository feature migration, context-bounded subagent delegation, non-one-to-one modernization, design-doc-driven implementation, CodeHub-backed migration through the matching CodeHub MCP, legacy smell remediation, 取其精华去其糟粕, subagent 分工迁移, 功能点拆分, 方案审批后迁移, 功能迁移, 特性迁移, 老仓功能探索, 旧系统升级到 2.0, 功能优化, 设计文档落地, or reconstruct a function from source code and deliver the intended 2.0 capability end to end in a new codebase.
---

# Migrate Feature To V2

Recover the legacy behavior from the source repository, split large work into bounded subagent task packages, split the explored feature points into focused Markdown artifacts, classify legacy code smells, extract the valuable essence, reject the dross, reconcile the evidence with the intended 2.0 design, then write an approvable migration design. Implement target code only after the design is approved. Treat source code as behavioral evidence, not as a template to paste; treat design documents as the intended future state, not optional commentary.

## Inputs And Defaults

Resolve these inputs before editing:

- **Source repository**: legacy repository path or URL used as read-only evidence.
- **Target repository**: AI-friendly 2.0 repository where implementation belongs.
- **Feature request**: user-visible capability, business rule, API, workflow, job, UI behavior, or named function to migrate.
- **Design documents**: optional PRD, technical design, API spec, OpenSpec change, ADR, issue, ticket, or acceptance document that defines the 2.0 target behavior.
- **Change intent**: whether the work is compatible migration, optimized behavior, redesigned workflow, API replacement, feature split/merge, deprecation, or greenfield implementation informed by legacy evidence.
- **Bad smell policy**: optional user guidance for which legacy smells, defects, or technical debt must be fixed during migration.
- **Approval requirement**: who or what can approve the migration design before implementation. Default to the current user when no other approval source is provided.
- **Subagent strategy**: whether to delegate exploration, design extraction, implementation slices, or verification to subagents. Default to subagents for broad migrations and to the same task-package protocol run serially when subagents are unavailable.
- **Acceptance criteria**: explicit requirements when provided; otherwise recover them from source behavior and tests.

Use the current workspace as the target repository when the user gives only a source repository. Treat a user-provided repository as the source unless they explicitly call it the 2.0 target. If both repository roles remain ambiguous and editing the wrong repository is plausible, ask one concise question before modifying code.

For remote URLs, clone or fetch only after obtaining any required approval. Do not modify or commit in the source repository unless the user explicitly requests it.

## Repository Access Rules

- Treat local paths as ordinary read-only source roots unless the user explicitly allows changes.
- Treat generic Git URLs as remote repositories that may require clone/fetch approval.
- Treat any URL or user label that identifies CodeHub as a CodeHub repository. Use the matching CodeHub MCP for repository metadata, branch discovery, file reads, code search, history, pull/merge request context, and permission-safe access.
- Do not silently downgrade a CodeHub URL to generic `git clone`, browser scraping, or unauthenticated HTTP access. If the matching CodeHub MCP is unavailable, use tool discovery or connector installation when possible; otherwise stop and ask the user to provide or enable the CodeHub MCP.
- When both CodeHub MCP evidence and local checkout evidence exist, record which source each claim came from.

## Non-Negotiables

- Preserve externally observable business behavior unless the user requests a behavior change.
- When design documents exist, implement the intended 2.0 behavior they specify while using the source repository to recover compatibility obligations and hidden business rules.
- When a design document or optimization request diverges from recovered source behavior, require explicit user confirmation unless the current task already clearly authorizes that exact divergence.
- When design documents and recovered source behavior are consistent, perform a complete migration of the feature, including edge cases, validations, permissions, persistence, side effects, configuration, observability, and tests.
- Do not assume a one-to-one migration. Explicitly decide whether each legacy behavior is preserved, changed, replaced, deprecated, split, merged, or dropped.
- Adapt the implementation to target conventions, ownership boundaries, frameworks, and existing abstractions.
- Take the essence and reject the dross: preserve domain rules, invariants, public contracts, proven edge cases, tests, and operational lessons; reject accidental architecture, copy-paste structure, obsolete dependencies, unsafe shortcuts, and brittle implementation mechanisms.
- Do not blindly copy source files, legacy architecture, generated code, obsolete dependencies, or known defects.
- Do not preserve legacy bad smells as compatibility. Fix simple low-risk smells in the target implementation, and remediate severe smells or defects instead of recreating them.
- Trace security, authorization, validation, transactions, idempotency, persistence, events, and integrations explicitly.
- Keep the target repository buildable throughout the migration and protect unrelated user changes.
- Add tests that prove the recovered contract and requested 2.0 behavior.
- Make intentional behavior differences explicit in the migration record and final report.
- Persist source exploration results before implementation so another agent or engineer can trace every recovered behavior back to source evidence.
- Split recovered feature points into small Markdown files and use those files, not raw sprawling exploration context, as the basis for target design.
- For large migrations, split work into bounded task packages and use subagents when available. Each subagent must receive only the minimal inputs for its package and must write a durable report or artifact.
- Do not modify target implementation code before the migration design is approved. Exploration artifacts and design documents may be written before approval.
- Interpret "AI-friendly" as discoverable, explicit, composable, testable, and observable. Do not add an LLM, agent endpoint, or weaken security merely to claim AI readiness.

## Context-Bounded Subagent Orchestration

Use subagents when the migration has multiple entry points, many candidate files, multiple target owners, large design documents, source/target repositories that cannot fit comfortably in one context, or repeated signs of context pressure. If subagents are not available, still use the same task packages and run them serially.

The main agent is the orchestrator:

- Own the user conversation, repository-role decisions, approval gates, final design, integration, and final report.
- Keep only the current request, `task-package-index.md`, `feature-point-index.md`, `migration-design.md`, `migration-record.md`, and the current task package in active context.
- Do not keep raw source dumps, broad search logs, full call chains, or subagent private reasoning in active context after their artifacts are written.
- Merge decisions only from persisted artifacts, evidence IDs, and concise subagent reports.

Before broad exploration or implementation, create or update:

- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-packages/TP-###-<name>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/subagent-reports/TP-###-<name>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md`

Each task package must state objective, role, allowed inputs, forbidden inputs/actions, scope boundaries, output paths, evidence format, stop conditions, acceptance checks, and context retirement rule. No package should ask a subagent to read the complete source repository, complete target repository, and complete design corpus at the same time unless that broad read is explicitly justified.

Recommended subagent roles:

- `source-entrypoint-explorer`: explore one source entry point, workflow, or domain slice; write feature-point Markdown and evidence.
- `design-intent-extractor`: read only design artifacts; write target intent, acceptance criteria, explicit changes, and questions.
- `legacy-smell-auditor`: inspect feature-point artifacts and source evidence; write smell classifications and remediation recommendations.
- `target-architecture-mapper`: read target analogs; write owner, boundary, pattern, and verification mapping.
- `reconciliation-designer`: combine reduced artifacts into the baseline-vs-target matrix and migration design.
- `implementation-slice-agent`: after approval, implement one approved slice with a disjoint write set and minimal source/design context.
- `verification-agent`: verify implementation, design approval, migration record, and test coverage against persisted artifacts.

Read `references/subagent-coordination.md` before delegating a broad migration.

## Workflow

### 1. Establish The Two-Repository Context

1. Resolve local source and target roots or remote repository identities and confirm their roles.
2. Locate and read user-provided design documents or discover likely design artifacts in the target repo when the request references them.
3. If the source or target is a CodeHub address, access it through the matching CodeHub MCP before attempting any generic Git operation.
4. Read repository instructions, manifests, architecture docs, and recent relevant changes in both repositories.
5. Inspect target worktree changes before editing. Never overwrite unrelated changes.
6. Profile both repositories when they are unfamiliar:

   `python3 <skill-dir>/scripts/profile_repositories.py --source <source-root> --target <target-root> --output-dir <target-root>/.ai-migrations/feature-migrations/<feature-slug>`
7. If the migration is broad, create the orchestration task-package index before expanding exploration.

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

For detailed design-doc reconciliation guidance, read `references/design-driven-modernization.md`. For broad design documents, delegate a `design-intent-extractor` package that outputs a compact design-intent artifact instead of carrying the whole document set forward.

### 3. Recover And Persist The Source Baseline

Start from user-visible or externally callable entry points, then trace inward:

1. Search for route paths, command names, UI labels, event names, configuration keys, database entities, logs, tests, and likely symbols with `rg`.
2. Follow the call chain through controllers/handlers, orchestration, domain logic, persistence, integrations, and emitted side effects.
3. Inspect tests, fixtures, schemas, API specifications, migrations, and configuration that constrain behavior.
4. Use `git log`, `git blame`, and historical diffs when current intent is unclear.
5. Record file-and-line evidence for each important behavior.

Persist the exploration as you go. Before implementation, create or update:

- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-exploration.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-evidence.json`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-point-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-points/<feature-point-slug>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/legacy-smells.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md`
- supporting artifacts such as `search-log.md`, `candidate-files.txt`, `call-trace.md`, or `codehub-mcp-evidence.md` when useful

Use the target repository's existing artifact directory if it has one. Read `references/source-exploration-contract.md` for the required structure.

Keep context bounded:

- Assign source exploration by entry point, workflow, domain concept, or integration boundary to `source-entrypoint-explorer` packages when one pass would overload context.
- After exploration, summarize each coherent feature point into its own Markdown file.
- Keep one feature point per file: entry points, behavior, data/integration evidence, essence/dross, smells, open questions, and verification ideas.
- Use `feature-point-index.md` as the navigation map. Load only the index and the feature-point files needed for the current design decision.
- Do not carry full raw source dumps, broad search logs, subagent conversations, or every inspected file in active context once the artifacts are written.

Recover at least:

- inputs, outputs, defaults, and error semantics
- permissions, validation, and security constraints
- state transitions, transactions, and idempotency
- persistence reads/writes and data shape
- synchronous and asynchronous side effects
- integration contracts, timeouts, retries, and fallback behavior
- configuration, flags, limits, and compatibility expectations
- observable logs, metrics, traces, and audit events

Separate **essence** from **dross**:

- Essence includes business rules, domain invariants, user-visible contracts, compatibility obligations, proven edge cases, useful tests, data constraints, operational signals, and production lessons.
- Dross includes accidental class/module layout, duplicated or tangled implementation, framework workarounds, obsolete dependencies, unsafe shortcuts, hidden globals, dead code, brittle orchestration, and known defects.

Do not preserve incidental class layouts, duplicated logic, or framework workarounds unless they are required for compatibility. Record each important take/drop decision in the exploration and migration records.

### 4. Classify And Remediate Legacy Smells

Build a legacy smell and dross inventory before target implementation. For large feature paths, delegate a `legacy-smell-auditor` package after feature-point Markdown files exist. Classify each item as:

- `simple-fix`: low-risk technical debt that can be corrected while preserving behavior, such as duplicated local logic, misleading names, small long-method extractions, magic constants, weak logging, missing null/empty guards, local exception handling cleanup, or obvious test fixture cleanup.
- `severe-fix`: serious design, correctness, security, reliability, performance, or data-integrity problems that must not be copied into 2.0, such as authorization bypasses, injection risks, transaction leaks, race/idempotency flaws, data corruption, resource leaks, unsafe retries, hard-coded secrets, unbounded queries, N+1 behavior, framework misuse, or highly coupled god-object logic.
- `defer-with-record`: known debt outside the feature slice or too risky to fix now; keep it out of the target implementation when possible and record the reason.
- `preserve-by-contract`: awkward legacy behavior that is externally required; preserve the behavior but avoid preserving the implementation smell.
- `dross-drop`: source structure, dependency, pattern, or workaround that has no business value and should not enter the target design.
- `essence-keep`: source insight or behavior that must influence the target implementation.

Apply these rules:

- Fix `simple-fix` smells directly in the target design and tests; do not ask unless the fix changes external behavior.
- Fix or redesign around `severe-fix` issues. Add tests or checks that prove the severe problem was not carried forward.
- Keep `essence-keep` items as target behavior, tests, contracts, or operational requirements.
- Drop `dross-drop` items from the target design and record why they are not migrated.
- If a severe fix changes an external contract, data compatibility, or user-visible behavior, use the divergence confirmation gate unless the current task explicitly authorizes the change.
- Do not edit the source repository to clean smells unless the user explicitly asks; remediation belongs in the target implementation and migration record.
- Read `references/legacy-smell-remediation.md` for the full classification checklist.

### 5. Reconcile Legacy Behavior With The Target Design

Build a baseline-vs-target matrix from the feature point Markdown files before implementation:

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

### 6. Map The Target Capability Onto The Target Architecture

Explore the target before designing. For broad targets, delegate one or more `target-architecture-mapper` packages by target owner or analogous feature:

1. Find the closest analogous feature and identify its entry-point, domain, persistence, integration, test, and observability patterns.
2. Reuse target-owned abstractions when they genuinely match the intended 2.0 responsibility.
3. Build a responsibility map: source responsibility, design requirement, target owner, implementation action, and verification.
4. Identify compatibility gaps in data models, APIs, event schemas, dependencies, or operational assumptions.
5. Prefer a thin adapter at a real boundary over spreading legacy assumptions through target code.

Do not create a parallel architecture just because the source repository used one.

### 7. Write The Migration Design For Approval

Before changing target implementation code, create:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-design.md`

Base the design on the split feature point Markdown files, the design documents, target architecture exploration, and the essence/dross decisions. Do not rely on unreduced raw exploration context as the design source of truth.

The design must include:

- scope and non-goals
- feature point summary with links to `feature-points/*.md`
- target architecture mapping
- behavior compatibility and intentional differences
- simple/severe legacy smell remediation decisions
- data, API, event, integration, rollout, and observability changes
- implementation slices
- task package plan that maps slices to subagent packages, allowed write sets, outputs, and verification
- verification plan
- open questions and approval status

Read `references/migration-design-approval.md` for the required design and approval record shape.

### 8. Get Approval Before Implementation

Pause after producing `migration-design.md` unless one of these is true:

- the current user explicitly approves the design in the conversation
- an existing approval artifact or ticket is provided and clearly authorizes the design
- the user explicitly pre-authorized implementation after design generation for this exact scope

Record approval in:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/design-approval.md`

If approval is partial, implement only the approved slices and task packages. If approval requests changes, update the feature point mapping, task-package plan, and migration design before proceeding.

### 9. Write A Migration And Design Record

Before substantial edits, create or update a migration record. Use the target repository's existing agent/workflow artifact convention when one exists; otherwise default to:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-record.md`

Include the legacy baseline, split feature point artifacts, subagent task ledger, context recovery ledger, design inputs, design approval, essence/dross decisions, legacy smell inventory, baseline-vs-target matrix, target mapping, intentional differences, risk decisions, implementation slices, and verification plan. Use `references/migration-record-contract.md` for the required shape.

Proceed autonomously through exploration and design artifacts when evidence supports it. Pause before implementation until design approval is recorded, and also pause when an unresolved ambiguity could materially change business behavior, security, data integrity, or the public contract.

### 10. Implement A Complete Vertical Slice

After design approval, implement the smallest complete approved slice that delivers the intended 2.0 capability through its real entry point. Use `implementation-slice-agent` packages for independent slices with disjoint write sets; each package must work from `migration-design.md`, `design-approval.md`, relevant feature-point files, and target owner context instead of reopening the full source exploration.

1. Add or update explicit contracts and schemas.
2. Implement domain behavior in the target's existing ownership boundaries according to the design decision matrix.
3. Wire persistence, integrations, configuration, dependency injection, routes, handlers, jobs, or UI as required.
4. Preserve or intentionally revise authorization, validation, transactional behavior, idempotency, and failure semantics according to the design record.
5. Add logs, metrics, traces, or audit events consistent with target conventions.
6. Remediate classified `simple-fix` and `severe-fix` smells in the target implementation.
7. Remove temporary duplication or compatibility scaffolding that is not needed after the slice works.

For detailed 2.0 design guidance, read `references/ai-friendly-v2.md` when choosing between multiple viable target designs.

### 11. Verify Behavior, Design, Smell Remediation, And Integration

Derive verification scenarios from both the target design and the recovered source baseline, not merely from copied source tests.

- Add focused unit tests for business rules and edge cases.
- Add integration or contract tests for boundaries changed by the migration.
- Use `verification-agent` packages for independent verification slices when test scope is broad or risk is high.
- Use differential, golden, or fixture-based comparison against the source for preserved behavior, and explicit new expectations for redesigned behavior.
- Run target formatting, static checks, build, and relevant tests; broaden checks when shared behavior changed.
- Search for missing registrations, routes, dependency injection wiring, schemas, migrations, flags, and documentation.
- Verify failure paths, authorization, idempotency, and side effects, not only the happy path.
- Verify compatibility adapters, deprecation paths, data migrations, rollout flags, and backfill behavior when the 2.0 design changes external contracts.
- For aligned behavior, verify complete migration coverage against the source baseline: all entry points, edge cases, validation failures, permissions, data mutations, emitted events, external calls, config-controlled behavior, logs, metrics, and audit output that matter externally.
- Verify that every `simple-fix` and `severe-fix` smell has a target-side remediation, test, static check, or documented reason when deferred.
- Verify implementation matches the approved `migration-design.md`; if the implementation must deviate, update the design and get approval before continuing.

If the source behavior cannot be executed, state which claims are proven by static evidence and which remain assumptions.

### 12. Report The Result

Report:

- design documents or optimization requirements used
- source entry points and strongest implementation evidence
- persisted source exploration artifact paths
- subagent task packages, reports, and context-recovery artifact paths
- feature point Markdown files used for design
- design approval source and approved implementation slices
- legacy smells fixed, severe issues remediated, and any deferred smells with reasons
- essence kept and dross intentionally rejected
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
- Preserve the source's business essence, not its accidental implementation shape.
- Reject source dross even when it is easy to copy.
- Design from the persisted feature point Markdown files, not from an overloaded in-memory exploration context.
- Use bounded task packages and subagents for broad migrations; if subagents are unavailable, run the same packages serially and keep the same artifacts.
- Do not implement until the migration design is approved or an explicit approval source is recorded.
- When source code contains simple low-risk smells, fix them in the target implementation as part of migration.
- When source code contains severe security, correctness, reliability, performance, or data-integrity problems, remediate them in the target design and record the decision.
- When a target abstraction almost fits but would distort the contract, add a narrow adapter or extend the abstraction with tests.
- When evidence is contradictory, prefer externally observable behavior and executable tests over comments or names.
- When the source contains an apparent defect, do not silently reproduce or silently fix it. Record the finding and choose based on compatibility requirements.
