# Design-Driven Modernization Guide

Use this guide when migration is not one-to-one, when the user provides a design document, or when the task includes feature optimization.

## Source Of Truth Order

Apply this order unless the user says otherwise. A design document can define the target state, but a design/source conflict is not automatically approved.

1. Explicit user instruction in the current task.
2. Current approved 2.0 design document or API/spec artifact, only for behavior changes that are explicitly confirmed or clearly requested.
3. Target repository architecture and current conventions.
4. Source repository observable behavior, tests, schemas, and production-facing contracts.
5. Source implementation details.

Security, privacy, data integrity, and compliance constraints override all of the above.

## Design Document Extraction

From each design artifact, extract:

- target user/business outcome
- public API, UI, event, job, or tool entry points
- entities, state transitions, and data ownership
- required compatibility with legacy callers, data, URLs, events, or reports
- intentional behavior changes and removed behavior
- rollout, migration, backfill, feature flag, and deprecation requirements
- acceptance criteria and test scenarios
- observability, audit, and operational expectations
- open questions and explicitly out-of-scope items

If the document contains multiple alternatives, identify which alternative is approved. If approval is unclear and the choice affects public behavior or data, ask before editing.

## Design And Source Alignment

Classify every meaningful behavior before implementation:

- **Aligned**: design and source agree. Migrate the complete source behavior and verify it.
- **Source-only**: source has behavior missing from the design. Preserve it unless the user confirms it should be removed or deprecated.
- **Design-only**: design adds behavior with no source equivalent. Implement it as new 2.0 scope.
- **Divergent**: design contradicts or changes source behavior. Ask for confirmation unless the current user request explicitly authorizes that exact change.
- **Dropped**: design removes source behavior. Ask for confirmation or cite documented approval.

For aligned behavior, "complete" means more than matching the main success path. Cover validation, authorization, idempotency, defaults, persistence, state transitions, side effects, integrations, configuration, logs, metrics, audits, and important error semantics.

## Migration Modes

### Compatible Migration

Use when the feature should behave the same from the outside.

- Preserve source contract.
- Modernize internals to fit the target architecture.
- Verify with source-derived tests and target integration tests.

### Compatible Enhancement

Use when the legacy contract remains but 2.0 adds capability.

- Keep old inputs and outputs valid.
- Add new fields, flows, or operations without breaking legacy callers.
- Test both legacy compatibility and new behavior.

### Behavior Replacement

Use when 2.0 intentionally changes the business behavior.

- Identify old scenarios that no longer apply.
- Add explicit tests for new expected behavior.
- Document compatibility impact and rollout requirements.
- Confirm the replacement before implementation when it contradicts recovered source behavior.

### Workflow Redesign

Use when the same business goal is implemented through a different user or system flow.

- Map legacy responsibilities to new workflow stages.
- Avoid forcing old controller/service/job boundaries into the target.
- Verify the end-to-end outcome rather than one-to-one method parity.

### Split Or Merge

Use when one source feature becomes multiple target capabilities, or several source features become one target capability.

- Create a responsibility map with one row per target owner.
- Preserve shared rules in one tested domain owner.
- Avoid duplicating legacy business rules across split paths.

### Deprecation

Use when old behavior remains only temporarily.

- Add adapters, warnings, feature flags, or compatibility shims only at stable boundaries.
- Track sunset criteria and tests for both old and new paths.
- Do not spread deprecated assumptions through new domain code.
- Confirm the deprecation before implementation when the source behavior is still externally reachable.

### Greenfield With Legacy Reference

Use when source code is evidence but not a blueprint.

- Extract business rules, edge cases, and operational constraints.
- Design natively in the target architecture.
- Do not recreate source module structure or dependency graph.

## Reconciliation Checklist

- Which source behaviors must remain externally compatible?
- Which source behaviors are intentionally optimized or removed?
- Which source/design differences have explicit user confirmation?
- Which design requirements have no source equivalent?
- Which source edge cases are missing from the design document?
- Which aligned behaviors still need full migration coverage?
- Which target abstractions already own each responsibility?
- Which data migrations, adapters, flags, or rollout steps are required?
- Which tests prove legacy compatibility and which prove redesigned behavior?
- Which differences need explicit user or stakeholder confirmation?
