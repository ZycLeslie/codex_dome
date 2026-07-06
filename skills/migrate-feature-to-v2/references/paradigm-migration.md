# Paradigm Migration

Use this guide when the source and target differ by language, framework, runtime, or architectural paradigm, such as Java service code migrating to an Airflow DAG.

## Required Artifact

Write or update:

```text
target-paradigm-map.md
```

Required sections:

```markdown
# <Feature> Target Paradigm Map

## Runtime Delta
| Source language/framework/runtime | Target language/framework/runtime | Migration mode | Consequence |
|---|---|---|---|

## Responsibility Mapping
| Source responsibility | Source evidence | Keep as behavior? | Target primitive | Target artifact | Drop/rewrite rationale | Verification |
|---|---|---|---|---|---|---|

## Source Shape Rejection
| Source shape/token | Why not target-native | Target replacement | Approval if preserved |
|---|---|---|---|

## Framework Semantics
| Concern | Source behavior | Target-native expression | Verification |
|---|---|---|---|
```

## Rules

- Treat source code as behavior evidence, not as an implementation blueprint.
- Do not port source classes, methods, package layout, DTO/service/repository hierarchy, framework lifecycles, or utility scaffolding line by line.
- Preserve domain rules, public contracts, data contracts, formulas, edge cases, retries, idempotency, and operational lessons.
- Re-express preserved behavior through target-owned primitives and conventions.
- Expect less target code when the target framework owns orchestration, lifecycle, dependency injection, retries, scheduling, or observability.
- If preserving a source-language shape is unavoidable, record the external contract and approval in `target-paradigm-map.md`.

## Airflow Targets

For Java-to-Airflow or service-to-DAG migrations, map behavior to Airflow primitives before writing code:

- DAG schedule, catchup, backfill, timezone, concurrency, max active runs
- tasks/operators, TaskFlow functions, sensors, hooks, connections, Variables, params, XCom, datasets
- retries, retry delay, timeout, SLA, pools, priority, trigger rules
- idempotency, partition/date handling, data quality checks, compensating behavior
- logs, metrics, alerts, lineage, ownership, runbook links

Do not recreate Java service layers inside Airflow unless the approved design says the DAG must call an existing service or shared library.

## Completion Blockers

- Missing `target-paradigm-map.md` for cross-language or cross-framework migration.
- Target patch keeps source-language structure without an approved compatibility reason.
- Airflow implementation hides business parameters, schedules, retries, connections, or data dependencies outside the DAG/config artifacts.
