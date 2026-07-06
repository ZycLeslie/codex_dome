# Legacy Smell Remediation

Use this guide when source exploration finds legacy code smells, defects, or technical debt in the feature path. The target implementation should preserve required business behavior and useful production lessons, not legacy implementation damage.

## Contents

- Classification
- Smell Inventory Fields
- Legacy Dross Firewall
- Smell-Audit Task Package Rules
- Decision Rules

## Classification

### simple-fix

Low-risk smells that can be fixed in the target implementation while preserving external behavior.

Examples:

- duplicated local logic
- misleading names
- small long-method extraction opportunities
- magic constants that should become named constants or configuration
- hard-coded absolute paths that clearly should become target configuration or repo-relative resources
- weak or noisy logging
- obvious missing null/empty guard where the behavior is clear
- duplicated frontend formatting, local state, or client-side validation that can be centralized without changing visible behavior
- local exception handling cleanup
- small test fixture or helper cleanup

Action:

- Fix directly in the target implementation.
- Add or update tests when the smell touches behavior.
- Record the fix in the migration record, but do not ask for confirmation unless external behavior changes.

### severe-fix

Serious problems that must not be copied into 2.0.

Examples:

- authorization or authentication bypass
- injection risks or unsafe deserialization
- transaction leaks, partial writes, or data corruption
- race conditions or idempotency flaws
- resource leaks or unbounded memory/file/network use
- hard-coded secrets or privileged endpoints
- hard-coded environment-specific filesystem paths, legacy service endpoints, or file URLs that can affect production behavior
- unsafe retries, duplicate side effects, or missing compensation
- unbounded queries, N+1 patterns, or severe performance cliffs
- frontend permission display that disagrees with server authorization, unsafe client-only validation, stale generated API clients, or UI flows that can submit invalid state
- framework misuse that breaks lifecycle, validation, transactions, caching, or security
- god-object logic or circular coupling that would damage target ownership

Action:

- Redesign or fix in the target implementation.
- Add tests, static checks, or integration checks proving the severe issue was not carried forward.
- Record the risk, remediation decision, compatibility impact, and verification.
- If remediation changes external contracts, data compatibility, or user-visible behavior, use the divergence confirmation gate unless the current task explicitly authorizes the change.

### defer-with-record

Debt discovered during exploration but outside the feature slice or too risky to fix in this migration.

Action:

- Do not recreate the smell in new target code when avoidable.
- Record why it is deferred, what risk remains, and the proposed follow-up.
- Avoid using deferred debt as a target design dependency.

### preserve-by-contract

Awkward behavior that looks like a smell but is externally required.

Action:

- Preserve the behavior through a clear contract or adapter.
- Do not preserve the bad implementation structure.
- Add tests that lock the required behavior.

### essence-keep

Source behavior or production knowledge that should survive migration.

Examples:

- domain invariants
- externally visible contracts
- edge cases proven by tests or production behavior
- operational signals that support support/compliance workflows
- historical compatibility rules still required by callers or data

Action:

- Preserve as target behavior, tests, contracts, or observability.
- Re-express through target architecture instead of copying source shape.

### dross-drop

Legacy implementation material with no target value.

Examples:

- accidental class/module layout
- copy-paste structure
- absolute filesystem paths such as `/Users/...`, `/home/...`, `/opt/...`, `/var/...`, or Windows drive paths
- `file://` URLs and generated source paths
- source repository paths, source package prefixes, and fully qualified class/module names copied as shortcuts
- source-language class/service/repository/DTO hierarchy copied into a different target framework
- old hostnames, hard-coded localhost endpoints, and environment-specific directory names
- obsolete dependencies
- framework workarounds no longer needed
- dead code and unused branches
- brittle orchestration created by historical constraints

Action:

- Do not migrate.
- Record why it is dropped when it appears in the feature path.
- Replace with target-owned configuration, imports, adapters, route names, storage abstractions, generated target clients, or repo-relative resources.
- Confirm only if dropping it could affect an external contract.

### needs-reconciliation

Use when an item looks like dross but might be externally visible.

Examples:

- a legacy path returned in an API response
- a fully qualified name used by external configuration
- a hard-coded URL consumed by another system
- a file path that appears in audit records or exported reports

Action:

- Do not copy it directly into target implementation.
- Add it to the baseline-vs-target matrix.
- Require an explicit decision: preserve through adapter, replace with target contract, deprecate, or drop.

## Smell Inventory Fields

Record each relevant smell with:

- smell/problem summary
- classification: `simple-fix`, `severe-fix`, `defer-with-record`, `preserve-by-contract`, `essence-keep`, `dross-drop`, or `needs-reconciliation`
- source evidence
- target remediation decision
- behavior compatibility impact
- verification command or test
- legacy dross scan status when the item is a path, package prefix, endpoint, generated path, or source-specific token

## Legacy Dross Firewall

Before implementation, list source-specific implementation tokens that must not leak into 2.0:

- source repository root or top-level module names
- source package prefixes and generated-code prefixes
- absolute filesystem path prefixes
- old service domains, base URLs, queue/topic names, bucket names, or local endpoints
- class names or fully qualified names that have no business meaning

After implementation, run:

```bash
python3 <skill-dir>/scripts/scan_legacy_dross.py \
  --target <target-root> \
  --legacy-token <source-package-or-path-prefix> \
  --output-md <target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/legacy-dross-scan.md
```

Every finding must be resolved before completion:

- `fixed`: replaced with target-native configuration, abstraction, import, or adapter.
- `approved-compatibility`: intentionally preserved because it is an external contract, with approval and tests.
- `deferred-with-record`: not fixed now, with risk and follow-up.

Unresolved findings mean the migration is not complete.

## Smell-Audit Task Package Rules

Use a `legacy-smell-auditor` package when the feature path is broad or when multiple feature-point files may contain quality, security, reliability, or data-integrity risks.

The smell auditor may:

- classify smells, dross, and essence from feature-point Markdown files and cited source evidence
- recommend target remediation and verification
- flag compatibility impact
- mark uncertain items as `needs-reconciliation`

The smell auditor must not:

- expand implementation scope without main-agent approval
- decide that externally visible behavior can be dropped
- edit target implementation code before design approval
- treat weak evidence as a confirmed severe defect

Each `severe-fix` recommendation must include source evidence, compatibility impact, target remediation, and verification. When it is unclear whether an item is required behavior or a smell, mark it `needs-reconciliation` and hand it to the design/source alignment stage.

## Decision Rules

- Never copy severe problems merely to match old code.
- Never copy legacy full paths, source package prefixes, or environment-specific identifiers merely because the source code used them.
- Never copy source-language layers into a different target paradigm, such as recreating Java service classes inside Airflow DAG code.
- Never use "AI-friendly" as an excuse to rewrite business behavior without confirmation.
- Prefer target-native ownership over source class/module shape.
- Preserve source business rules and edge cases, but replace unsafe or brittle implementation mechanisms.
- Convert source essence into target-native contracts, tests, and observability.
- Drop source dross deliberately instead of recreating it for convenience.
- When unsure whether something is behavior or smell, treat it as behavior until evidence or user confirmation says otherwise.
