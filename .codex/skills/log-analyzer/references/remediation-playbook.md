# Remediation Playbook

Load this file when the log summary is clear but the next engineering step is not.

## Search Recipes

- Search the exact sample message first.
- If no exact hit exists, search stable fragments and logger names.
- Search the exception class even when the message is dynamic.
- Read the logging call and the nearest `catch`, `throw`, `raise`, retry, or HTTP mapping code together.

## Common Fix Patterns

### Noisy logs

- Repeated `INFO` or `DEBUG` in hot paths usually suggests lowering the level, adding sampling, or moving the log behind a state change.
- Repeated `WARN` without operator action usually suggests either promoting to `ERROR` with alerting or downgrading to `INFO` if it is expected.
- Duplicate stack traces for the same failure usually suggest logging once at the boundary instead of at each layer.

### Validation and nullability failures

- `NullPointerException`, `TypeError`, `AttributeError`, and similar failures often point to missing input validation, stale assumptions, or incomplete fallback handling.
- Look for missing guards near request parsing, cache lookups, optional fields, and third-party responses.

### Timeout and dependency failures

- `Timeout`, `ConnectException`, `SocketException`, `BrokenPipe`, and DNS failures often point to retry policy issues, pool exhaustion, or too-short deadlines.
- Inspect timeout values, retry fan-out, circuit breaker behavior, and whether failures are logged with enough dependency context.

### Database and storage failures

- Constraint violations usually point to duplicate writes, missing idempotency, or stale assumptions about data shape.
- Lock or transaction timeouts suggest long transactions, missing indexes, or high-contention update patterns.

### Parsing and schema drift

- JSON, XML, and serialization errors often point to upstream schema changes or partial payloads.
- Recommend capturing offending field names, payload shape, version metadata, and tolerant parsing where appropriate.

### Authentication and authorization failures

- Repeated auth failures often need clearer principal identifiers, token expiry context, and separation between expected denials and unexpected system errors.
- Search where auth exceptions are translated into HTTP or RPC responses so the logging level matches intent.

## Reporting Guidance

- Recommend one code change, one logging change, and one verification step whenever possible.
- Separate confirmed findings from likely causes.
- If the code match is weak, say what additional artifact would reduce uncertainty: config, request sample, deployment version, or more complete stack trace.
