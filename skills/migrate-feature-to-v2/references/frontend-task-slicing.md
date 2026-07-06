# Frontend Task Slicing

Use this guide when a migration has a frontend surface and ordinary project discovery would consume too much context. The goal is to recover and implement browser-visible behavior without asking any one agent to understand the entire frontend application.

## Contents

- Frontend Rule
- Required Artifacts
- Thin Index First
- Resume And Subagent Gate
- Micro-Package Types
- One-Pass Feasibility Thresholds
- Allowed And Forbidden Inputs
- Frontend Feature Point Shape
- Implementation Slices
- Verification Slices

## Frontend Rule

Never start frontend migration by reading the whole frontend project, whole `src/pages`, whole `src/components`, whole store tree, or whole generated client tree. First create a thin index from small, high-signal sources, then split the feature by visible user path and technical responsibility.

The main agent should keep only:

- the user request
- `migration-status.md`
- `source-exploration/frontend/frontend-surface-index.md`
- `source-exploration/feature-point-index.md`
- `orchestration/task-checklist.md`
- the current frontend task package

Retire broad route dumps, dependency graphs, and search logs after writing artifacts.

## Required Artifacts

Create these under the migration workspace when frontend is present or unknown:

```text
source-exploration/frontend/
  frontend-surface-index.md
  frontend-task-map.md
  frontend-open-questions.md
```

Use existing target artifact conventions when the repository already has them.

## Thin Index First

The first frontend package is an indexer, not a full explorer.

Allowed discovery sources:

- package manifest and frontend framework config
- route registry, router files, app shell, menu/sidebar config
- feature flags, permission gates, i18n/message keys
- page filenames and test filenames from `rg --files`
- targeted `rg` for route paths, UI labels, API operation names, store names, query keys, event names, and feature terms
- one nearest analogous target feature, if needed for pattern mapping

The indexer should write:

```markdown
# <Feature> Frontend Surface Index

## Frontend Presence
| Surface | Present? | Evidence | Notes |
|---|---|---|---|

## Route And Navigation Candidates
| Route/menu/entry | Files | Evidence | Confidence |
|---|---|---|---|

## Page Or Container Candidates
| Candidate | Direct files only | Why relevant | Split package |
|---|---|---|---|

## Component Candidates
| Component | Direct files only | Role | Split package |
|---|---|---|---|

## State/API Candidates
| Store/query/API/type | Files | Contract hint | Split package |
|---|---|---|---|

## Visible States And UX
| State/message/permission/analytics | Evidence | Split package |
|---|---|---|

## Do Not Load Yet
| Path or tree | Reason |
|---|---|
```

## Resume And Runner Gate

After interruption, context compression, a fresh session, or a failed long frontend attempt, frontend work must return to orchestration before more code edits:

1. Reload `resume.md`, `migration-status.md`, `orchestration/task-checklist.md`, `orchestration/subagent-assignment-queue.md`, and `frontend-surface-index.md`.
2. Mark any active frontend package `stale` if its allowed inputs, write set, or design approval are unclear.
3. Split stale or broad packages into micro-packages.
4. Add every frontend micro-package to `subagent-assignment-queue.md` with runner `multica` when available, otherwise `subagent`.
5. Dispatch frontend packages through `multica` when available, otherwise one subagent package at a time; require persisted reports before the next package or batch starts.

The main agent must not continue frontend implementation directly after resume. It may only update artifacts, split packages, review reports, and make a tiny non-behavioral edit when the checklist explicitly marks that edit as non-frontend and one-pass-feasible.

If neither `multica` nor subagent capability is available, mark frontend packages blocked; do not silently continue in main-agent serial mode.

## Micro-Package Types

Prefer these frontend packages over one broad `frontend-surface-explorer` package:

| Package type | Scope | Must output |
|---|---|---|
| `frontend-route-indexer` | Route, menu, feature flag, permission gate, i18n key, and candidate file map | `frontend-surface-index.md`, candidate packages |
| `frontend-page-explorer` | One route page/container and direct imports only | page feature point, visible behavior, direct dependencies |
| `frontend-component-explorer` | One component cluster with bounded direct children | props/events/slots, user interactions, visible states |
| `frontend-state-api-explorer` | One store/query/mutation/API-client/generated-type path | request/response mapping, cache/invalidation, errors |
| `frontend-form-validation-explorer` | One form or validation path | fields, defaults, validation messages, submit behavior |
| `frontend-visible-state-explorer` | Loading, empty, error, permission, disabled, accessibility, i18n, analytics, or telemetry behavior | visible-state feature point |
| `frontend-implementation-slice-agent` | One approved frontend slice with a disjoint write set | patch, tests, report |
| `frontend-verification-agent` | One frontend verification layer | test output, browser/manual scenario, gaps |

## One-Pass Feasibility Thresholds

A frontend package is `no-needs-split` when it requires any of these:

- reading more than one route workflow
- reading more than one page/container cluster
- reading more than one store/query/API-client path
- editing more than one page/container, more than one component cluster, or a page plus state/API plus tests together
- reading broad directories such as all of `src/pages`, `src/components`, `src/store`, `src/api`, or generated clients
- inspecting more than about 8 source files before writing a useful artifact
- tracing both UI behavior and backend/domain behavior in the same package
- modifying route wiring, state/API, page UI, and tests together
- continuing after the package already consumed too much context in a previous session

Mark the package `risky` only when the file count is slightly high but the stop conditions and output artifact are narrow. Otherwise split before execution.

## Allowed And Forbidden Inputs

Allowed inputs for a frontend micro-package:

- the package file
- `frontend-surface-index.md`
- relevant frontend feature-point files
- relevant design excerpt or design-intent artifact
- one nearest target analog, if named by the package
- exact files listed by the package

Forbidden by default:

- full frontend source tree reads
- broad component library exploration
- broad generated client exploration
- unrelated routes and pages
- backend source exploration unless the package is explicitly an end-to-end coordination package
- implementation edits before design approval

## Frontend Feature Point Shape

Keep each frontend feature point small:

```markdown
# <Feature Point>

## Summary
- ID:
- Surface: frontend
- Type: route | page | component | state-api | form-validation | visible-state | test
- Status:

## Direct Files
| File | Role | Evidence |
|---|---|---|

## Visible Behavior
| Scenario | User action/state | Expected UI | Evidence |
|---|---|---|---|

## API And State
| Concern | Source/target file | Notes |
|---|---|---|

## Validation And Messages
| Field/state | Message/default | Evidence |
|---|---|---|

## Essence And Dross
| Item | Classification | Decision |
|---|---|---|

## Verification Ideas
| Check | Tool or test layer |
|---|---|
```

## Implementation Slices

After design approval, split frontend implementation by write set:

- route/menu/permission/i18n wiring
- page/container data orchestration
- component rendering and interaction
- form defaults, validation, submit/disable behavior
- state/query/mutation/API client integration
- generated types or typed adapter usage
- loading/empty/error/permission states
- accessibility and analytics hooks
- unit/component tests
- browser/E2E or integration tests

Do not combine all of these in one implementation package unless the feature is trivially small and the one-pass feasibility check says `yes`.

After resume, even a small frontend implementation slice should be dispatched through `multica` when available or as `frontend-implementation-slice-agent` otherwise, unless it is a one-line mechanical fix with no behavior impact and no frontend context needed.

## Verification Slices

Frontend verification should cover:

- route or navigation entry is reachable
- initial loading, empty, error, permission, and success states
- form defaults, required fields, validation messages, submit disable/enable behavior
- API request parameters, response mapping, error mapping, and cache invalidation
- visible text, i18n keys, accessibility-critical labels, analytics hooks when present
- frontend tests and, when backend is involved, end-to-end contract behavior

Completion is blocked when a present frontend surface has no feature point, no task package, no implementation decision, or no verification/defer record.
