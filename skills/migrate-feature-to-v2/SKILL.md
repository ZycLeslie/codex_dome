---
name: migrate-feature-to-v2
description: Discover a named legacy feature, split large work into bounded subagent task packages, assess whether each task can finish in one pass, track task checklists, separate frontend/backend surfaces when present, persist source evidence, split feature points into Markdown, reconcile with 2.0 design docs, reject legacy dross and smells, write an approvable migration design, then implement only after approval. Use for cross-repository feature migration, full-stack frontend/backend migration, context-bounded subagent delegation, non-one-to-one modernization, CodeHub-backed migration through the matching MCP, legacy smell remediation, 取其精华去其糟粕, 任务清单跟踪, 一次性完成评估, 前后端分开迁移, subagent 分工迁移, 功能点拆分, 方案审批后迁移, 功能迁移, 旧系统升级到 2.0, 功能优化, or reconstructing a feature end to end.
---

# Migrate Feature To V2

Recover the legacy behavior from the source repository, split large work into bounded subagent task packages, assess each task for one-pass feasibility, track every task in a durable checklist, separate frontend and backend surfaces when both exist, split the explored feature points into focused Markdown artifacts, classify legacy code smells, extract the valuable essence, reject the dross, reconcile the evidence with the intended 2.0 design, then write an approvable migration design. Implement target code only after the design is approved. Treat source code as behavioral evidence, not as a template to paste; treat design documents as the intended future state, not optional commentary.

## Inputs And Defaults

Resolve these inputs before editing:

- **Source repository**: legacy repository path or URL used as read-only evidence.
- **Target repository**: AI-friendly 2.0 repository where implementation belongs.
- **Feature request**: user-visible capability, business rule, API, workflow, job, UI behavior, or named function to migrate.
- **Design documents**: optional PRD, technical design, API spec, OpenSpec change, ADR, issue, ticket, or acceptance document that defines the 2.0 target behavior.
- **Change intent**: whether the work is compatible migration, optimized behavior, redesigned workflow, API replacement, feature split/merge, deprecation, or greenfield implementation informed by legacy evidence.
- **Feature surfaces**: frontend, backend/API, jobs, events, integrations, data, configuration, and observability surfaces involved in the capability.
- **Bad smell policy**: optional user guidance for which legacy smells, defects, or technical debt must be fixed during migration.
- **Approval requirement**: who or what can approve the migration design before implementation. Default to the current user when no other approval source is provided.
- **Subagent strategy**: whether to delegate exploration, design extraction, implementation slices, or verification to subagents. Default to subagents for broad migrations and to the same task-package protocol run serially when subagents are unavailable.
- **Task tracking strategy**: where to maintain task checklist, one-pass feasibility decisions, and final completion check. Default to the migration orchestration artifacts.
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
- Do not collapse full-stack work into backend-only migration. If the feature has frontend and backend behavior, explore, design, implement, and verify them as separate coordinated slices.
- Adapt the implementation to target conventions, ownership boundaries, frameworks, and existing abstractions.
- Take the essence and reject the dross: preserve domain rules, invariants, public contracts, proven edge cases, tests, and operational lessons; reject accidental architecture, copy-paste structure, obsolete dependencies, unsafe shortcuts, and brittle implementation mechanisms.
- Do not blindly copy source files, legacy architecture, generated code, obsolete dependencies, or known defects.
- Do not copy legacy implementation identifiers into 2.0 by default. Absolute filesystem paths, Windows paths, `file://` URLs, source repository paths, source package prefixes, fully qualified class names used as shortcuts, legacy hostnames, and hard-coded environment paths are dross unless explicitly proven to be an external contract.
- Do not preserve legacy bad smells as compatibility. Fix simple low-risk smells in the target implementation, and remediate severe smells or defects instead of recreating them.
- Trace security, authorization, validation, transactions, idempotency, persistence, events, and integrations explicitly.
- Keep the target repository buildable throughout the migration and protect unrelated user changes.
- Add tests that prove the recovered contract and requested 2.0 behavior.
- Make intentional behavior differences explicit in the migration record and final report.
- Persist source exploration results before implementation so another agent or engineer can trace every recovered behavior back to source evidence.
- Split recovered feature points into small Markdown files and use those files, not raw sprawling exploration context, as the basis for target design.
- For large migrations, split work into bounded task packages and use subagents when available. Each subagent must receive only the minimal inputs for its package and must write a durable report or artifact.
- Before executing any task package, assess whether it can be completed in one pass with the available context, tools, permissions, and dependencies. If not, split it before work starts.
- Maintain a durable task checklist and update it after every package, context handoff, approval change, implementation slice, and verification run.
- Record feature surface coverage. If a frontend, UI route, page, component, state transition, validation message, permission display, API call, generated client, or end-to-end flow exists, it must be represented in feature points, task packages, design, implementation, and verification.
- Do not declare completion until a final completion check proves that all required tasks, feature points, surfaces, approved slices, and verification items are complete or explicitly deferred with reasons.
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
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-packages/TP-###-<name>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/subagent-reports/TP-###-<name>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/completion-check.md`

Each task package must state objective, role, one-pass feasibility, allowed inputs, forbidden inputs/actions, scope boundaries, output paths, evidence format, stop conditions, acceptance checks, checklist update rule, and context retirement rule. No package should ask a subagent to read the complete source repository, complete target repository, and complete design corpus at the same time unless that broad read is explicitly justified.

One-pass feasibility must answer:

- Can this package reasonably finish in one pass without overloading context?
- Are required inputs, permissions, tools, approvals, and dependencies available?
- Is the write set disjoint and small enough for safe implementation or review?
- What is the split plan if the answer is no?

Keep `task-checklist.md` as the source of truth for package status. The checklist should include package ID, surface, objective, one-pass feasibility, dependencies, status, owner/subagent, artifacts, verification, and final check status.

Recommended subagent roles:

- `source-entrypoint-explorer`: explore one source entry point, workflow, or domain slice; write feature-point Markdown and evidence.
- `frontend-surface-explorer`: explore UI routes, pages, components, forms, state management, client-side validation, generated clients, permission display, analytics, and browser-visible behavior.
- `backend-surface-explorer`: explore API handlers, domain services, persistence, jobs, events, integrations, auth, transactions, idempotency, and server-side observability.
- `design-intent-extractor`: read only design artifacts; write target intent, acceptance criteria, explicit changes, and questions.
- `legacy-smell-auditor`: inspect feature-point artifacts and source evidence; write smell classifications and remediation recommendations.
- `legacy-dross-auditor`: inspect source feature points and target changes for copied implementation details such as full paths, source package prefixes, hard-coded endpoints, and obsolete wiring.
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

Identify the feature surfaces before deep exploration. Check whether the capability includes frontend routes, pages, components, forms, state, client APIs, generated clients, backend APIs, domain services, persistence, jobs, events, external integrations, data migrations, configuration, or observability. If both frontend and backend exist, create separate feature-point files and task packages for each layer plus an end-to-end coordination package.

Before starting any exploration package, create or update `task-checklist.md`. Mark packages as `ready`, `needs-split`, `blocked`, `in-progress`, `done`, `verified`, or `deferred`. If a task is `needs-split`, split it and update the checklist before assigning it to a subagent or executing it serially.

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

1. Search for route paths, command names, UI labels, component names, client API calls, event names, configuration keys, database entities, logs, tests, and likely symbols with `rg`.
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
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md`
- supporting artifacts such as `search-log.md`, `candidate-files.txt`, `call-trace.md`, or `codehub-mcp-evidence.md` when useful

Use the target repository's existing artifact directory if it has one. Read `references/source-exploration-contract.md` for the required structure.

Keep context bounded:

- Assign source exploration by entry point, workflow, domain concept, or integration boundary to `source-entrypoint-explorer` packages when one pass would overload context.
- For full-stack features, assign frontend and backend exploration separately. Do not let a backend package claim the feature is migrated until the frontend surface has been checked or explicitly recorded as not applicable.
- After exploration, summarize each coherent feature point into its own Markdown file.
- Keep one feature point per file: entry points, behavior, data/integration evidence, essence/dross, smells, open questions, and verification ideas.
- Use `feature-point-index.md` as the navigation map. Load only the index and the feature-point files needed for the current design decision.
- Update `task-checklist.md` whenever a feature point is discovered, split, completed, verified, or deferred.
- Do not carry full raw source dumps, broad search logs, subagent conversations, or every inspected file in active context once the artifacts are written.

Recover at least:

- inputs, outputs, defaults, and error semantics
- frontend routes, pages, components, forms, client state, generated clients, browser-visible validation, loading/empty/error states, permissions display, and analytics or telemetry hooks
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
- Implementation-detail dross includes absolute paths, source repository paths, source package/class prefixes, file URLs, hard-coded local endpoints, environment-specific directories, generated-code paths, and all source naming that has no business meaning.

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
- Treat ugly full paths, hard-coded filesystem paths, source package prefixes, and source repo-specific identifiers as `dross-drop` by default. Replace them with target-native configuration, aliases, imports, adapters, routing, storage abstractions, or generated target types.
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

1. Find the closest analogous feature and identify its frontend, backend/API, domain, persistence, integration, test, and observability patterns.
2. Reuse target-owned abstractions when they genuinely match the intended 2.0 responsibility.
3. Build a responsibility map: source responsibility, surface, design requirement, target owner, implementation action, and verification.
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
- surface coverage for frontend, backend/API, jobs/events, integrations, data, configuration, observability, and end-to-end flows
- target architecture mapping
- behavior compatibility and intentional differences
- simple/severe legacy smell remediation decisions
- legacy dross firewall decisions: copied-looking paths, fully qualified names, source package prefixes, hard-coded endpoints, and their target replacements
- data, API, event, integration, rollout, and observability changes
- implementation slices split by surface when applicable, especially frontend and backend/API
- task package plan that maps slices to subagent packages, allowed write sets, outputs, and verification
- one-pass feasibility and split decision for every package
- task checklist coverage for every feature point, surface, and approved slice
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

If approval is partial, implement only the approved slices and task packages. If approval requests changes, update the feature point mapping, task-package plan, task checklist, and migration design before proceeding.

### 9. Write A Migration And Design Record

Before substantial edits, create or update a migration record. Use the target repository's existing agent/workflow artifact convention when one exists; otherwise default to:

`<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-record.md`

Include the legacy baseline, split feature point artifacts, subagent task ledger, task checklist, context recovery ledger, design inputs, design approval, essence/dross decisions, legacy smell inventory, baseline-vs-target matrix, target mapping, intentional differences, risk decisions, implementation slices, and verification plan. Use `references/migration-record-contract.md` for the required shape.

Proceed autonomously through exploration and design artifacts when evidence supports it. Pause before implementation until design approval is recorded, and also pause when an unresolved ambiguity could materially change business behavior, security, data integrity, or the public contract.

### 10. Implement A Complete Vertical Slice

After design approval, implement the smallest complete approved slice that delivers the intended 2.0 capability through its real entry point. Use `implementation-slice-agent` packages for independent slices with disjoint write sets; each package must work from `migration-design.md`, `design-approval.md`, relevant feature-point files, and target owner context instead of reopening the full source exploration.

Before starting each implementation package, re-check one-pass feasibility against current code, approvals, dependencies, and worktree state. If the package no longer fits in one pass, split it, mark the old package `stale` or `needs-split`, and update `task-checklist.md`.

For full-stack features, implement coordinated but separate slices:

- frontend slice: routes, pages, components, forms, client state, API client usage, generated types, validation presentation, loading/empty/error states, permissions display, accessibility, and frontend tests
- backend slice: API contracts, handlers, domain behavior, persistence, jobs/events, integrations, authorization, validation, transactions, idempotency, observability, and backend tests
- end-to-end slice: contract alignment, user workflow, request/response compatibility, error display, rollout flags, and end-to-end or integration verification

1. Add or update explicit contracts and schemas.
2. Implement domain behavior in the target's existing ownership boundaries according to the design decision matrix.
3. Wire persistence, integrations, configuration, dependency injection, routes, handlers, jobs, or UI as required.
4. Preserve or intentionally revise authorization, validation, transactional behavior, idempotency, and failure semantics according to the design record.
5. Add logs, metrics, traces, or audit events consistent with target conventions.
6. Remediate classified `simple-fix` and `severe-fix` smells in the target implementation.
7. Replace copied legacy paths, package prefixes, fully qualified names, and environment-specific constants with target-owned abstractions or configuration.
8. Remove temporary duplication or compatibility scaffolding that is not needed after the slice works.

For detailed 2.0 design guidance, read `references/ai-friendly-v2.md` when choosing between multiple viable target designs.

### 11. Verify Behavior, Design, Smell Remediation, And Integration

Derive verification scenarios from both the target design and the recovered source baseline, not merely from copied source tests.

- Add focused unit tests for business rules and edge cases.
- Add frontend tests when a UI or browser/client surface exists, including visible states and user interactions.
- Add integration or contract tests for boundaries changed by the migration.
- Use `verification-agent` packages for independent verification slices when test scope is broad or risk is high.
- Use differential, golden, or fixture-based comparison against the source for preserved behavior, and explicit new expectations for redesigned behavior.
- Run target formatting, static checks, build, and relevant tests; broaden checks when shared behavior changed.
- Search for missing registrations, routes, dependency injection wiring, schemas, migrations, flags, and documentation.
- Verify failure paths, authorization, idempotency, and side effects, not only the happy path.
- Verify compatibility adapters, deprecation paths, data migrations, rollout flags, and backfill behavior when the 2.0 design changes external contracts.
- Verify end-to-end behavior across frontend and backend when both exist; do not declare completion from backend tests alone.
- For aligned behavior, verify complete migration coverage against the source baseline: all entry points, edge cases, validation failures, permissions, data mutations, emitted events, external calls, config-controlled behavior, logs, metrics, and audit output that matter externally.
- Verify that every `simple-fix` and `severe-fix` smell has a target-side remediation, test, static check, or documented reason when deferred.
- Run the legacy dross scan against target code after implementation:

  `python3 <skill-dir>/scripts/scan_legacy_dross.py --target <target-root> --output-md <target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/legacy-dross-scan.md`

  Add `--legacy-token <source-package-or-path-prefix>` for known source-specific package names, repo paths, domains, or generated prefixes. Review every finding; fix it, mark it as approved compatibility, or defer it with evidence before completion.
- Verify implementation matches the approved `migration-design.md`; if the implementation must deviate, update the design and get approval before continuing.
- Run a final checklist pass against `task-checklist.md`, `feature-point-index.md`, `migration-design.md`, `design-approval.md`, `migration-record.md`, and verification results. Write the result to `orchestration/completion-check.md`.

If the source behavior cannot be executed, state which claims are proven by static evidence and which remain assumptions.

### 12. Report The Result

Report:

- design documents or optimization requirements used
- source entry points and strongest implementation evidence
- persisted source exploration artifact paths
- subagent task packages, reports, and context-recovery artifact paths
- task checklist and completion-check artifact paths
- feature point Markdown files used for design
- design approval source and approved implementation slices
- legacy smells fixed, severe issues remediated, and any deferred smells with reasons
- legacy dross scan results and every copied-looking path or source-specific token that was fixed, approved as compatibility, or deferred
- essence kept and dross intentionally rejected
- target files and architecture owners changed
- frontend/backend surface coverage, or evidence that a surface is not applicable
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
- When a feature has both frontend and backend surfaces, split them into separate coordinated slices and verify the end-to-end user workflow.
- Preserve the source's business essence, not its accidental implementation shape.
- Reject source dross even when it is easy to copy.
- Treat copied legacy full paths, hard-coded endpoints, source package prefixes, and source repo-specific identifiers as defects in the migration unless the migration design explicitly approves them as compatibility.
- Design from the persisted feature point Markdown files, not from an overloaded in-memory exploration context.
- Use bounded task packages and subagents for broad migrations; if subagents are unavailable, run the same packages serially and keep the same artifacts.
- Split any task that is not feasible to finish in one pass before assigning or executing it.
- Keep the task checklist current; when context is compressed or work is handed off, reload from the checklist and current package instead of reconstructing from memory.
- Treat the final completion check as the last gate before saying the migration is done.
- Do not implement until the migration design is approved or an explicit approval source is recorded.
- When source code contains simple low-risk smells, fix them in the target implementation as part of migration.
- When source code contains severe security, correctness, reliability, performance, or data-integrity problems, remediate them in the target design and record the decision.
- When a target abstraction almost fits but would distort the contract, add a narrow adapter or extend the abstraction with tests.
- When evidence is contradictory, prefer externally observable behavior and executable tests over comments or names.
- When the source contains an apparent defect, do not silently reproduce or silently fix it. Record the finding and choose based on compatibility requirements.
