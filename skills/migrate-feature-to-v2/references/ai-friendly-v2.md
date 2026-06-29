# AI-Friendly 2.0 Design Guide

Use this guide when multiple target designs can preserve or intentionally improve the same business capability. AI-friendly code remains ordinary production-quality code; it is easier for both humans and automated agents to discover, call, reason about, test, and observe.

## Design Priorities

Apply these priorities in order:

1. Preserve security, privacy, compliance, and data integrity.
2. Implement the approved 2.0 design intent, including intentional behavior changes.
3. Preserve legacy compatibility where required by design, rollout, callers, or data contracts.
4. Follow target repository conventions and architecture.
5. Make contracts and ownership explicit.
6. Improve composability, discoverability, tests, and observability.
7. Avoid unnecessary novelty and migration scope.

## Preferred Properties

### Discoverable

- Give the feature a clear entry point and stable owner.
- For full-stack features, make both frontend entry points and backend/API entry points discoverable and connected by explicit contracts.
- Use names that reflect business concepts rather than historical implementation details.
- Keep route, command, event, configuration, and schema definitions near their owners or linked through established target conventions.
- Add concise documentation only where repository conventions expect it.

### Explicit

- Represent inputs, outputs, errors, events, and configuration with types or schemas where the target supports them.
- Make defaults, limits, timeouts, retries, and feature flags visible.
- Prefer explicit dependency injection and registration over hidden global state or string-based reflection.
- Model important state transitions and authorization decisions directly.
- When behavior changes from legacy, encode the new contract in schemas, tests, docs, or migration records rather than leaving it as an implicit code difference.
- When legacy code uses brittle, unsafe, or tightly coupled mechanisms, expose the target behavior through explicit contracts instead of recreating the mechanism.

### Composable

- Keep orchestration separate from pure business decisions and infrastructure boundaries.
- Expose narrow programmatic interfaces that can be reused by APIs, jobs, tools, or future agent workflows without duplicating business logic.
- Make operations deterministic where the domain permits it.
- Isolate nondeterministic I/O, time, randomness, and external services behind testable boundaries.

### Testable

- Encode recovered behavior as focused tests and realistic boundary tests.
- When a frontend exists, test user-visible states and interactions in addition to backend business rules.
- Make fixtures and examples small, readable, and representative.
- Support deterministic substitutes for time, IDs, external calls, and event delivery where target patterns allow.
- Test authorization, validation, idempotency, error paths, and side effects.
- Separate tests that protect legacy compatibility from tests that assert redesigned 2.0 behavior.

### Observable

- Emit structured logs, metrics, traces, and audit events using target conventions.
- Include stable identifiers needed to correlate a feature operation without exposing secrets.
- Make partial failure and retry outcomes visible.
- Preserve operational signals that existing support or compliance workflows rely on.
- Add new signals for redesigned workflows, rollout flags, adapters, and deprecation paths.

## Avoid

- Adding an LLM or agent dependency when the feature does not require one.
- Creating a generic "AI service" layer with no concrete ownership.
- Exposing privileged internal operations through a new endpoint merely for agent access.
- Replacing typed or validated interfaces with free-form prompts.
- Hiding business rules inside framework callbacks, reflection, dynamic strings, or untestable glue.
- Splitting code into many tiny modules that obscure the end-to-end workflow.
- Recreating source architecture inside the target as a permanent compatibility island.
- Treating a design document as implementation-complete when legacy edge cases, compatibility obligations, or operational constraints still need source evidence.
- Carrying forward severe legacy smells such as authorization gaps, transaction leaks, unbounded queries, hard-coded secrets, unsafe retries, or god-object coupling.

## Design Review Questions

- Can an engineer find the feature from its public entry point and trace it to its business owner?
- Can another caller reuse the business capability without bypassing authorization or duplicating rules?
- Are inputs, outputs, errors, state transitions, and side effects explicit?
- If both frontend and backend exist, are their contracts, visible states, and end-to-end flow verified?
- Can tests run deterministically without real external services?
- Can operators understand success, failure, retry, and partial completion?
- Does the design look native to the target repository?
- Are intentional differences from legacy behavior visible, tested, and traceable to a design decision?
