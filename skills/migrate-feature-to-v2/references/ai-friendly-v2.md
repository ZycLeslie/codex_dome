# AI-Friendly 2.0 Design Guide

Use this guide when multiple target designs can preserve the same business behavior. AI-friendly code remains ordinary production-quality code; it is easier for both humans and automated agents to discover, call, reason about, test, and observe.

## Design Priorities

Apply these priorities in order:

1. Preserve business behavior, security, and data integrity.
2. Follow target repository conventions and architecture.
3. Make contracts and ownership explicit.
4. Improve composability, discoverability, tests, and observability.
5. Avoid unnecessary novelty and migration scope.

## Preferred Properties

### Discoverable

- Give the feature a clear entry point and stable owner.
- Use names that reflect business concepts rather than historical implementation details.
- Keep route, command, event, configuration, and schema definitions near their owners or linked through established target conventions.
- Add concise documentation only where repository conventions expect it.

### Explicit

- Represent inputs, outputs, errors, events, and configuration with types or schemas where the target supports them.
- Make defaults, limits, timeouts, retries, and feature flags visible.
- Prefer explicit dependency injection and registration over hidden global state or string-based reflection.
- Model important state transitions and authorization decisions directly.

### Composable

- Keep orchestration separate from pure business decisions and infrastructure boundaries.
- Expose narrow programmatic interfaces that can be reused by APIs, jobs, tools, or future agent workflows without duplicating business logic.
- Make operations deterministic where the domain permits it.
- Isolate nondeterministic I/O, time, randomness, and external services behind testable boundaries.

### Testable

- Encode recovered behavior as focused tests and realistic boundary tests.
- Make fixtures and examples small, readable, and representative.
- Support deterministic substitutes for time, IDs, external calls, and event delivery where target patterns allow.
- Test authorization, validation, idempotency, error paths, and side effects.

### Observable

- Emit structured logs, metrics, traces, and audit events using target conventions.
- Include stable identifiers needed to correlate a feature operation without exposing secrets.
- Make partial failure and retry outcomes visible.
- Preserve operational signals that existing support or compliance workflows rely on.

## Avoid

- Adding an LLM or agent dependency when the feature does not require one.
- Creating a generic "AI service" layer with no concrete ownership.
- Exposing privileged internal operations through a new endpoint merely for agent access.
- Replacing typed or validated interfaces with free-form prompts.
- Hiding business rules inside framework callbacks, reflection, dynamic strings, or untestable glue.
- Splitting code into many tiny modules that obscure the end-to-end workflow.
- Recreating source architecture inside the target as a permanent compatibility island.

## Design Review Questions

- Can an engineer find the feature from its public entry point and trace it to its business owner?
- Can another caller reuse the business capability without bypassing authorization or duplicating rules?
- Are inputs, outputs, errors, state transitions, and side effects explicit?
- Can tests run deterministically without real external services?
- Can operators understand success, failure, retry, and partial completion?
- Does the design look native to the target repository?
