# Multica Orchestration

Use this guide when `multica` is available or the user asks to open multiple agent jobs. Multica is an optional dispatch backend; the migration workspace remains the source of truth.

## Required Artifacts

Use the normal package queue plus a multica job ledger:

```text
orchestration/subagent-assignment-queue.md
orchestration/multica-jobs.md
orchestration/subagent-reports/TP-###-<name>.md
```

`multica-jobs.md`:

```markdown
# <Feature> Multica Jobs

## Dispatch Policy
- Enabled? yes | no | unavailable
- Max parallel jobs:
- Current batch:

## Jobs
| Package | Role | Multica job ID | Allowed inputs | Write set | Status | Report path | Merge decision |
|---|---|---|---|---|---|---|---|

## Batch Barriers
| Barrier | Reason | Blocks packages |
|---|---|---|
```

## Dispatch Rules

- Dispatch only packages that already have a task-package file, one-pass feasibility, allowed inputs, write set, output path, stop conditions, and acceptance checks.
- Batch only independent packages. Do not run packages in parallel when they share a write set, depend on each other, need the same approval, or modify the same contract.
- Do not dispatch implementation packages before `migration-design.md` and `design-approval.md` approve the slice.
- Pass each job only the package file plus explicitly allowed artifacts.
- Require every job to write a report under `orchestration/subagent-reports/`.
- Main agent must reconcile reports, update checklist/status/timeline/resume, and decide merge order.

## Resume Rules

On resume, before opening new jobs:

1. Load `subagent-assignment-queue.md`, `multica-jobs.md`, `task-checklist.md`, and active package files.
2. Reconcile every multica job as `queued`, `running`, `completed`, `partial`, `blocked`, `failed`, or `stale`.
3. Do not redispatch a package with an unknown or running job unless the old job is explicitly abandoned in `multica-jobs.md`.
4. Mark downstream packages `stale` when a completed report changes design, contracts, target ownership, or write sets.

## Completion Blockers

- A multica job has no durable report.
- A job modified files outside its approved write set.
- Parallel jobs touched the same contract or write set without a recorded merge decision.
- `multica-jobs.md`, `subagent-assignment-queue.md`, and `task-checklist.md` disagree.
