---
name: migrate-feature-to-v2
description: Move a legacy feature into an AI-friendly 2.0 repo. Use for 功能迁移, 旧系统升级到 2.0, source spec/design first, cross-language or cross-framework migration, Java-to-Airflow style paradigm changes, full-stack migration, frontend micro-slicing, multica-first dispatch with subagent fallback, CodeHub MCP access, config inventory, coverage checks, design approval, and legacy dross cleanup.
---

# Migrate Feature To V2

Recover legacy behavior as evidence, reconcile it with 2.0 design docs, split work into bounded task packages, and implement only after approval. Keep evidence, task state, resume state, frontend slices, subagent reports, smell/dross decisions, and verification in project-local artifacts.

## Inputs And Defaults

Resolve these inputs before editing:

- **Source repository**: legacy repository path or URL used as read-only evidence.
- **Target repository**: AI-friendly 2.0 repository where implementation belongs.
- **Feature request**: user-visible capability, business rule, API, workflow, job, UI behavior, or named function to migrate.
- **Source specs and design docs**: existing source-repository specs, API contracts, ADRs, PRDs, runbooks, or test plans that describe the legacy feature.
- **Design documents**: optional PRD, technical design, API spec, OpenSpec change, ADR, issue, ticket, or acceptance document that defines the 2.0 target behavior.
- **Change intent**: whether the work is compatible migration, optimized behavior, redesigned workflow, API replacement, feature split/merge, deprecation, or greenfield implementation informed by legacy evidence.
- **Feature surfaces**: frontend, backend/API, jobs, events, integrations, data, configuration, and observability surfaces involved in the capability.
- **Source and target paradigm**: source language/framework/runtime and target language/framework/runtime, especially when they differ.
- **Bad smell policy**: optional user guidance for which legacy smells, defects, or technical debt must be fixed during migration.
- **Approval requirement**: who or what can approve the migration design before implementation. Default to the current user when no other approval source is provided.
- **Agent dispatch strategy**: whether to delegate exploration, design extraction, implementation slices, or verification through `multica`, subagents, or serial task packages. Default to `multica` when available; fall back to subagents when `multica` is unavailable; use serial execution only for small non-mandatory packages.
- **Migration workspace**: project-local artifact directory used as the visual dashboard and restart point. Default to `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/` unless the target repo already has an established artifact convention.
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

## Project-Local Visual Migration Workspace

Every migration must have a human-readable workspace inside the target repository before broad exploration, design, or implementation work expands. Use the target repository's existing agent, migration, or design artifact convention when one exists. Otherwise use:

```text
<target-root>/.ai-migrations/feature-migrations/<feature-slug>/
```

Initialize or refresh the workspace before broad exploration, preferably with:

```bash
python3 <skill-dir>/scripts/init_migration_workspace.py \
  --feature "<feature name>" \
  --source <source-root-or-url>
```

When running outside the target repository root, add `--target <target-root>`. The script defaults `--target` to the current directory.

The workspace is the visible control panel and the restart anchor:

- `README.md`: dashboard with current gate, phase summary, quick links, and next action.
- `migration-status.md`: visual status board for phases, surfaces, feature points, packages, approvals, and verification.
- `artifact-index.md`: index of every migration artifact, purpose, status, owner, and update time.
- `timeline.md`: append-only timeline of discoveries, decisions, approvals, splits, implementation slices, and verification runs.
- `resume.md`: minimal restart instructions, canonical reload set, active package, next action, and blockers.
- `source-exploration/` and `orchestration/`: source baseline, evidence, feature points, smells, task packages, reports, recovery, and completion check.

Update `README.md`, `migration-status.md`, `artifact-index.md`, `timeline.md`, and `resume.md` after every package result, approval change, implementation slice, verification run, context handoff, or pause. If the agent is interrupted, restarted, or context-compressed, reload `resume.md`, `migration-status.md`, `artifact-index.md`, `orchestration/task-checklist.md`, and the current package before continuing.

## Non-Negotiables

- Preserve externally observable business behavior unless the user requests a behavior change.
- When design documents exist, implement the intended 2.0 behavior they specify while using the source repository to recover compatibility obligations and hidden business rules.
- When a design document or optimization request diverges from recovered source behavior, require explicit user confirmation unless the current task already clearly authorizes that exact divergence.
- When design documents and recovered source behavior are consistent, perform a complete migration of the feature, including edge cases, validations, permissions, persistence, side effects, configuration, observability, and tests.
- Before deep source-code exploration, index source-repository specs, designs, and API contracts. If none exist or coverage is insufficient, dispatch 2-3 detailed exploration packages through `multica` first, otherwise subagents.
- Do not assume a one-to-one migration. Explicitly decide whether each legacy behavior is preserved, changed, replaced, deprecated, split, merged, or dropped.
- Do not collapse full-stack work into backend-only migration. If the feature has frontend and backend behavior, explore, design, implement, and verify them as separate coordinated slices.
- Adapt the implementation to target conventions, ownership boundaries, frameworks, and existing abstractions.
- When source and target differ by language, framework, runtime, or architecture, treat source code as behavior evidence only. Do not port source-language classes, methods, package layout, or framework scaffolding line by line.
- Take the essence and reject the dross: preserve domain rules, invariants, public contracts, proven edge cases, tests, and operational lessons; reject accidental architecture, copy-paste structure, obsolete dependencies, unsafe shortcuts, and brittle implementation mechanisms.
- Do not blindly copy source files, legacy architecture, generated code, obsolete dependencies, or known defects.
- Do not copy legacy implementation identifiers into 2.0 by default. Absolute filesystem paths, Windows paths, `file://` URLs, source repository paths, source package prefixes, fully qualified class names used as shortcuts, legacy hostnames, and hard-coded environment paths are dross unless explicitly proven to be an external contract.
- Do not preserve legacy bad smells as compatibility. Fix simple low-risk smells in the target implementation, and remediate severe smells or defects instead of recreating them.
- Trace security, authorization, validation, transactions, idempotency, persistence, events, and integrations explicitly.
- List third-party configuration center dependencies before implementation. Include keys, namespaces/groups, profiles/environments, defaults, ownership, sensitivity, target mappings, and rollout requirements; code migration is not complete while required external config is missing.
- Keep the target repository buildable throughout the migration and protect unrelated user changes.
- Add tests that prove the recovered contract and requested 2.0 behavior.
- Make intentional behavior differences explicit in the migration record and final report.
- Keep the migration process visible in a project-local workspace. Do not rely on chat history, private subagent context, or memory as the only record of current status, next action, approvals, or recovered behavior.
- After interruption, context compression, or a fresh session, do not continue implementation directly in the main agent. First run the resume gate, rebuild the subagent assignment queue, and delegate executable packages.
- Persist source exploration results before implementation so another agent or engineer can trace every recovered behavior back to source evidence.
- Split recovered feature points into small Markdown files and use those files, not raw sprawling exploration context, as the basis for target design.
- For large migrations, split work into bounded task packages and delegate them through `multica` when available, otherwise through subagents. Each job/subagent must receive only the minimal inputs for its package and must write a durable report or artifact.
- Probe `multica` before assigning subagents. When `multica` is available, use it as the preferred batch dispatcher for independent task packages; keep `subagent-assignment-queue.md`, `multica-jobs.md`, reports, checklist, and resume state authoritative.
- When a task is frontend, broad, post-resume, or already caused context pressure, delegated execution is mandatory. Use `multica` first, fall back to subagents, and do not silently downgrade to main-agent serial execution; if neither runner is available, record the blocker and ask for the capability to be enabled.
- For frontend work, do not spend a task package on understanding the whole frontend project. First create a thin frontend surface index, then split into route, page/container, component, state/API, form/validation, visible-state, accessibility/analytics, and frontend-test packages as applicable.
- Before executing any task package, assess whether it can be completed in one pass with the available context, tools, permissions, and dependencies. If not, split it before work starts.
- Maintain a durable task checklist and update it after every package, context handoff, approval change, implementation slice, and verification run.
- Maintain a feature coverage matrix for entry points, parameters, defaults, validation, branches, errors, side effects, config, schedules, and runtime controls. Missing or unverified rows block completion.
- Record feature surface coverage. If a frontend, UI route, page, component, state transition, validation message, permission display, API call, generated client, or end-to-end flow exists, it must be represented in feature points, task packages, design, implementation, and verification.
- Do not declare completion until a final completion check proves that all required tasks, feature points, surfaces, approved slices, and verification items are complete or explicitly deferred with reasons.
- Do not modify target implementation code before the migration design is approved. Exploration artifacts and design documents may be written before approval.

## Context-Bounded Subagent Orchestration

Use `multica` or subagents when the migration has multiple entry points, many candidate files, multiple target owners, large design documents, source/target repositories that cannot fit comfortably in one context, or repeated signs of context pressure. Prefer `multica` when available; otherwise use subagents. Serial execution is allowed only for small, non-frontend, non-resume packages that are explicitly one-pass-feasible. If neither `multica` nor subagents are available for mandatory delegated work, mark the package blocked instead of continuing in the main context.

The main agent is the orchestrator:

- Own the user conversation, repository-role decisions, approval gates, final design, integration, and final report.
- Keep only the current request, `task-package-index.md`, `feature-point-index.md`, `migration-design.md`, `migration-record.md`, and the current task package in active context.
- Do not keep raw source dumps, broad search logs, full call chains, or subagent private reasoning in active context after their artifacts are written.
- Merge decisions only from persisted artifacts, evidence IDs, and concise subagent reports.

Before broad exploration or implementation, create or update:

- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/README.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-status.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/artifact-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/timeline.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/resume.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md` and `task-checklist.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/subagent-assignment-queue.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/multica-jobs.md` when `multica` is used
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

Mirror checklist progress into the workspace dashboard files so a human can see the migration state without reading every package file. `resume.md` must always identify the next artifact to load and the next package or gate to work on.

Resume gate:

- Load `resume.md`, `migration-status.md`, `artifact-index.md`, `orchestration/task-checklist.md`, `orchestration/subagent-assignment-queue.md`, `orchestration/multica-jobs.md`, and only the current package artifacts.
- Re-evaluate one-pass feasibility and mark stale or oversized packages before any code edits.
- Assign every frontend package, every implementation package, every verification package, and every package with context pressure to runner `multica` when available; otherwise assign a subagent owner.
- Update `subagent-assignment-queue.md` with package, role, runner, allowed inputs, write set, status, and expected report path; reconcile `orchestration/multica-jobs.md` before opening new multica jobs.
- Main agent may only orchestrate, split, review reports, update records, and perform tiny non-frontend mechanical edits that are explicitly one-pass-feasible. It must not implement frontend slices after resume.

Recommended subagent roles:

- `source-doc-extractor`: index existing source specs, design docs, API contracts, and gaps; write `source-docs-index.md` before broad code exploration.
- `source-entrypoint-explorer`: explore one source entry point, workflow, or domain slice; write feature-point Markdown and evidence.
- `frontend-surface-explorer`: explore UI routes, pages, components, forms, state management, client-side validation, generated clients, permission display, analytics, and browser-visible behavior.
- `frontend-route-indexer`: build a thin route/menu/feature-flag/auth/i18n index without reading the whole frontend project.
- `frontend-page-explorer`: inspect one page or route container and its direct imports only.
- `frontend-state-api-explorer`: inspect one store/query/mutation/API-client/generated-type path for the feature.
- `frontend-form-visibility-explorer`: inspect one form, validation path, visible message set, loading/empty/error/permission state, accessibility hook, or analytics hook.
- `backend-surface-explorer`: explore API handlers, domain services, persistence, jobs, events, integrations, auth, transactions, idempotency, and server-side observability.
- `config-center-explorer`: list third-party config center providers, keys, namespaces/groups, profiles/envs, defaults, target mappings, owners, sensitivity, dynamic refresh, and missing config blockers.
- `target-paradigm-mapper`: map source responsibilities to target-native framework primitives when language, framework, runtime, or architecture differs.
- `coverage-matrix-verifier`: verify entry points, parameters, branches, errors, side effects, config, schedules, and runtime controls against the target design and patch.
- `design-intent-extractor`: read only design artifacts; write target intent, acceptance criteria, explicit changes, and questions.
- `legacy-smell-auditor`: inspect feature-point artifacts and source evidence; write smell classifications and remediation recommendations.
- `legacy-dross-auditor`: inspect source feature points and target changes for copied implementation details such as full paths, source package prefixes, hard-coded endpoints, and obsolete wiring.
- `target-architecture-mapper`: read target analogs; write owner, boundary, pattern, and verification mapping.
- `reconciliation-designer`: combine reduced artifacts into the baseline-vs-target matrix and migration design.
- `implementation-slice-agent`: after approval, implement one approved slice with a disjoint write set and minimal source/design context.
- `verification-agent`: verify implementation, design approval, migration record, and test coverage against persisted artifacts.

Read `references/source-doc-first.md` before broad source exploration. Read `references/subagent-coordination.md` before delegating or resuming. Read `references/multica-orchestration.md` before choosing a runner. Read `references/frontend-task-slicing.md` before frontend exploration or implementation larger than one route/page/component. Read `references/paradigm-migration.md` when source and target differ. Read `references/feature-coverage-matrix.md` for multi-input or branchy features. Read `references/config-center-inventory.md` when config is present or unknown.

## Workflow

### 1. Establish The Two-Repository Context

1. Resolve local source and target roots or remote repository identities and confirm their roles.
2. Locate and read user-provided design documents or discover likely design artifacts in the target repo when the request references them.
3. If the source or target is a CodeHub address, access it through the matching CodeHub MCP before attempting any generic Git operation.
4. Identify source and target language, framework, runtime, and architecture. If they differ, mark the migration as `cross-language`, `cross-framework`, or `paradigm rewrite`.
5. Read repository instructions, manifests, architecture docs, and recent relevant changes in both repositories.
6. Inspect target worktree changes before editing. Never overwrite unrelated changes.
7. Create or update the project-local migration workspace and dashboard. Use `scripts/init_migration_workspace.py` unless the target repository already has a stronger artifact convention.
8. Index source-repository specs, design docs, API contracts, ADRs, runbooks, and test plans into `source-exploration/source-docs-index.md`. If they are absent, stale, or insufficient, create 2-3 bounded exploration packages before broad code reading.
9. Profile both repositories when they are unfamiliar:

   `python3 <skill-dir>/scripts/profile_repositories.py --source <source-root> --target <target-root> --output-dir <target-root>/.ai-migrations/feature-migrations/<feature-slug>`
10. If the migration is broad, create the orchestration task-package index before expanding exploration.

Use the profile as orientation only. Read actual source files before making decisions.

Identify the feature surfaces before deep exploration. Check whether the capability includes frontend routes, pages, components, forms, state, client APIs, generated clients, backend APIs, domain services, persistence, jobs, events, external integrations, data migrations, configuration, or observability. If a frontend exists, create a thin frontend surface index before reading page/component internals. If both frontend and backend exist, create separate feature-point files and task packages for each layer plus an end-to-end coordination package.

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

- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/README.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/migration-status.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/artifact-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/timeline.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/resume.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-docs-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-exploration.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/source-evidence.json`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-point-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-points/<feature-point-slug>.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/coverage/feature-coverage-matrix.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/target-paradigm-map.md` when source and target paradigm differ
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/frontend/frontend-surface-index.md` when frontend is present or unknown
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/frontend/frontend-task-map.md` when frontend work needs multiple packages
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/config/config-center-inventory.md` when any config surface or third-party config center exists or is unknown
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/source-exploration/legacy-smells.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/subagent-assignment-queue.md`
- `<target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md`
- supporting artifacts such as `search-log.md`, `candidate-files.txt`, `call-trace.md`, or `codehub-mcp-evidence.md` when useful

Use the target repository's existing artifact directory if it has one. Read `references/source-exploration-contract.md` for the required structure.

Keep context bounded:

- Use `source-docs-index.md` as the first reduced source context. When docs are missing or weak, assign 2-3 targeted exploration packages instead of scanning the whole repo in one context.
- Assign source exploration by entry point, workflow, domain concept, or integration boundary to `source-entrypoint-explorer` packages when one pass would overload context.
- For full-stack features, assign frontend and backend exploration separately. Do not let a backend package claim the feature is migrated until the frontend surface has been checked or explicitly recorded as not applicable.
- For frontend features, first write `source-exploration/frontend/frontend-surface-index.md` from route tables, menu config, labels, feature flags, test names, and targeted `rg` results. Do not read entire `src/pages`, `src/components`, `src/store`, or generated client trees in a single package.
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
- third-party config center entries such as Nacos, Apollo, Spring Cloud Config, Consul, etcd, Vault, Kubernetes ConfigMap/Secret, or platform config: key, namespace/group, profile/env, default, target value, owner, sensitivity, rollout, and verification
- every externally meaningful parameter, field, default, validation rule, branch, error, side effect, schedule, retry, and runtime control
- observable logs, metrics, traces, and audit events

Separate **essence** from **dross**:

- Essence includes business rules, domain invariants, user-visible contracts, compatibility obligations, proven edge cases, useful tests, data constraints, operational signals, and production lessons.
- Dross includes accidental class/module layout, duplicated or tangled implementation, framework workarounds, obsolete dependencies, unsafe shortcuts, hidden globals, dead code, brittle orchestration, and known defects.
- Implementation-detail dross includes absolute paths, source repository paths, source package/class prefixes, file URLs, hard-coded local endpoints, environment-specific directories, generated-code paths, and all source naming that has no business meaning.

Do not preserve incidental class layouts, duplicated logic, or framework workarounds unless they are required for compatibility. Record each important take/drop decision in the exploration and migration records.

For cross-language or cross-framework migration, build `target-paradigm-map.md` before design approval. A Java-to-Airflow migration, for example, should map source responsibilities to DAGs, tasks/operators, sensors, hooks/connections, Variables, params, XCom, datasets, retries, backfill, idempotency, data checks, and alerts instead of recreating Java service layers in Python. Read `references/paradigm-migration.md` for the required mapping.

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
- target paradigm mapping when language, framework, runtime, or architecture differs
- behavior compatibility and intentional differences
- feature coverage matrix status for parameters, branches, side effects, schedules, and runtime controls
- frontend thin index and micro-package map when frontend is present or unknown
- third-party config center inventory and target environment mapping
- simple/severe legacy smell remediation decisions
- legacy dross firewall decisions: copied-looking paths, fully qualified names, source package prefixes, hard-coded endpoints, and their target replacements
- data, API, event, integration, rollout, and observability changes
- implementation slices split by surface when applicable, especially frontend and backend/API
- task package plan that maps slices to multica/subagent packages, allowed write sets, outputs, and verification
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

Include the legacy baseline, split feature point artifacts, visual workspace status, subagent task ledger, task checklist, context recovery ledger, design inputs, design approval, essence/dross decisions, legacy smell inventory, baseline-vs-target matrix, target mapping, intentional differences, risk decisions, implementation slices, and verification plan. Use `references/migration-record-contract.md` for the required shape.

The migration record should link to the workspace dashboard files and summarize their current status instead of duplicating every row.

Proceed autonomously through exploration and design artifacts when evidence supports it. Pause before implementation until design approval is recorded, and also pause when an unresolved ambiguity could materially change business behavior, security, data integrity, or the public contract.

### 10. Implement A Complete Vertical Slice

After design approval, implement the smallest complete approved slice that delivers the intended 2.0 capability through its real entry point. Use `implementation-slice-agent` packages for independent slices with disjoint write sets; each package must work from `migration-design.md`, `design-approval.md`, relevant feature-point files, and target owner context instead of reopening the full source exploration.

Before starting each implementation package, re-check one-pass feasibility against current code, approvals, dependencies, and worktree state. If the package no longer fits in one pass, split it, mark the old package `stale` or `needs-split`, and update `task-checklist.md`.

After resume or previous context pressure, implementation packages must be executed by `multica` when available or subagents otherwise. The main agent should not keep writing implementation code package after package; it should dispatch bounded packages, read persisted reports, update the checklist, then dispatch the next package or batch.

For full-stack features, implement coordinated but separate slices:

- frontend slices: route/menu wiring, page/container, leaf components, form/validation, state/query/mutation/API client, generated type usage, loading/empty/error states, permissions display, accessibility, analytics, and frontend tests. Keep each slice small enough to understand and edit in one pass.
- backend slice: API contracts, handlers, domain behavior, persistence, jobs/events, integrations, authorization, validation, transactions, idempotency, observability, and backend tests
- end-to-end slice: contract alignment, user workflow, request/response compatibility, error display, rollout flags, and end-to-end or integration verification

1. Add or update explicit contracts and schemas.
2. Implement domain behavior in the target's existing ownership boundaries according to the design decision matrix.
3. Wire persistence, integrations, configuration, dependency injection, routes, handlers, jobs, or UI as required.
4. Preserve or intentionally revise authorization, validation, transactional behavior, idempotency, and failure semantics according to the design record.
5. Add logs, metrics, traces, or audit events consistent with target conventions.
6. Remediate classified `simple-fix` and `severe-fix` smells in the target implementation.
7. Replace copied legacy paths, package prefixes, fully qualified names, and environment-specific constants with target-owned abstractions or configuration.
8. For cross-language or cross-framework migration, implement target-native primitives from `target-paradigm-map.md`; expect smaller target code when the target framework owns orchestration, lifecycle, retries, scheduling, or observability.
9. Remove temporary duplication or compatibility scaffolding that is not needed after the slice works.

### 11. Verify Behavior, Design, Smell Remediation, And Integration

Derive verification scenarios from both the target design and the recovered source baseline, not merely from copied source tests.

- Add focused unit tests for business rules and edge cases.
- Add frontend tests when a UI or browser/client surface exists, including visible states and user interactions.
- Add integration or contract tests for boundaries changed by the migration.
- Use `verification-agent` packages for independent verification slices when test scope is broad or risk is high.
- Use differential, golden, or fixture-based comparison against the source for preserved behavior, and explicit new expectations for redesigned behavior.
- Run target formatting, static checks, build, and relevant tests; broaden checks when shared behavior changed.
- Verify required third-party config exists or is explicitly deferred: config center namespace/group/profile, keys, secrets, feature flags, dynamic refresh behavior, target values, and owner approvals.
- Verify `source-exploration/coverage/feature-coverage-matrix.md`: every entry point, parameter, default, validation rule, branch, error, side effect, schedule, retry, and runtime control must be implemented, intentionally changed, approved for defer/drop, and tested.
- For cross-language or cross-framework migration, verify the target patch against `target-paradigm-map.md` and reject source-language structure copied without approval.
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
- visual migration workspace, persisted source exploration, status, artifact index, timeline, and resume paths
- multica/subagent task packages, reports, and context-recovery artifact paths
- runner assignment queue status, including any blocked delegated packages
- third-party config center inventory, target mappings, and any missing config blockers
- task checklist and completion-check artifact paths
- feature point Markdown files used for design
- design approval source and approved implementation slices
- legacy smells, severe issues, dross scan findings, copied-looking paths, and source-specific tokens that were fixed, approved, or deferred
- essence kept and dross intentionally rejected
- target files and architecture owners changed
- frontend/backend surface coverage, or evidence that a surface is not applicable
- preserved behaviors, optimized behaviors, deprecated behaviors, and intentional differences
- verification commands and outcomes
- remaining assumptions, risks, and follow-up work

## Decision Rules

- Do not treat a design/source conflict as approved just because it appears in a document. Ask for confirmation unless the current user request explicitly authorizes that specific behavior change.
- When source behavior and design intent agree, migrate the complete feature contract before calling the work done.
- When source and target language/framework/runtime differ, design from target primitives first. Source implementation shape is dross unless approved as an external contract.
- When the feature depends on a third-party config center, list and map the external config before implementation; missing config is a runtime blocker, not documentation follow-up.
- When parameters, branches, or side effects are numerous, a completed coverage matrix is mandatory before implementation and before final completion.
- When a feature has both frontend and backend surfaces, split them into separate coordinated slices and verify the end-to-end user workflow.
- When frontend project understanding alone would consume the context, stop broad reading, write or refresh the thin frontend surface index, and split into micro-packages before continuing.
- When resuming after interruption, force runner assignment before implementation. A frontend package owned by `main-agent` after resume is a process defect and blocks completion.
- Preserve the source's business essence, not its accidental implementation shape.
- Reject source dross even when it is easy to copy.
- Treat copied legacy full paths, hard-coded endpoints, source package prefixes, and source repo-specific identifiers as defects in the migration unless the migration design explicitly approves them as compatibility.
- Design from the persisted feature point Markdown files, not from an overloaded in-memory exploration context.
- Use bounded task packages with `multica` first and subagents as fallback for broad migrations. Serial execution is allowed only for small, non-frontend, non-resume packages that are explicitly one-pass-feasible.
- Do not use main-agent serial execution as a fallback for resumed frontend or broad implementation work. Block and request `multica` or subagent capability instead.
- Split any task that is not feasible to finish in one pass before assigning or executing it.
- Keep the task checklist current; when context is compressed or work is handed off, reload from the checklist and current package instead of reconstructing from memory.
- Keep the visual workspace current; when context is compressed, interrupted, or handed off, reload from `resume.md` and `migration-status.md` before opening broad source or target context again.
- Treat the final completion check as the last gate before saying the migration is done.
- Do not implement until the migration design is approved or an explicit approval source is recorded.
- When source code contains simple low-risk smells, fix them in the target implementation as part of migration.
- When source code contains severe security, correctness, reliability, performance, or data-integrity problems, remediate them in the target design and record the decision.
- When evidence is contradictory, prefer externally observable behavior and executable tests over comments or names.
- When the source contains an apparent defect, do not silently reproduce or silently fix it. Record the finding and choose based on compatibility requirements.
