---
name: log-analyzer
description: Analyze a directory of application logs, including plain log files and compressed archives, summarize repeated log patterns, exception hot spots, and noisy loggers, then correlate those findings with the current code repository to suggest likely fixes, instrumentation improvements, and log hygiene changes. Use when Codex is asked to inspect log dumps, support bundles, incident packages, or runtime traces and turn them into actionable engineering guidance.
---

# Log Analyzer

Analyze a log directory with the bundled script first, then trace the highest-signal findings back to the code repository and recommend concrete fixes.

## Quick Start

1. Identify the log root directory.
2. Run:
   `python3 .codex/skills/log-analyzer/scripts/analyze_logs.py "<log-dir>" --json --top 30`
3. Read the JSON summary and focus on:
   - `top_messages`
   - `exception_types`
   - `exceptions`
   - `noisiest_sources`
   - `skipped_inputs`
4. Correlate the hot spots with the repository by searching for exact log text, stable message fragments, logger names, and exception classes.
5. Return a concise report with evidence, likely code locations, and remediation suggestions.

## Workflow

### 1. Scan the logs

- The helper script supports common plain-text logs and archives:
  - `.log`, `.txt`, `.out`, `.err`, `.trace`, `.json`, `.ndjson`
  - `.gz`, `.bz2`, `.xz`
  - `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`
- The script normalizes volatile values such as timestamps, UUIDs, IDs, URLs, and paths so repeated messages group together.
- The script detects common Java, Python, Node, and generic `*Exception` or `*Error` signatures.

### 2. Decide what matters

Prioritize in this order:

- repeated `ERROR` or `FATAL`
- repeated exception groups
- high-volume `WARN`
- unexpectedly noisy `INFO` or `DEBUG`
- single files or archive members that dominate total event count

### 3. Trace findings back to code

Use `rg` instead of broad manual reading.

- Search the exact sample message first when it looks literal:
  `rg -n --hidden --glob '!*.log' 'user not found for tenant' <repo>`
- If the exact string does not match, search stable fragments from the normalized pattern.
  - Drop placeholders like `<num>`, `<uuid>`, `<path>`, and `<time>`.
  - Search logger names, endpoint paths, table names, job names, and exception classes.
- Search common logging and error sites:
  - `logger.error`, `logger.warn`, `logger.info`
  - `log.error`, `log.warn`, `LOG.error`
  - `throw new <ExceptionType>`
  - `raise <ExceptionType>`
- Read only the few best candidates before concluding.

### 4. Turn findings into recommendations

Tie each recommendation to evidence from both sides:

- log evidence: count, severity, sample message, stack preview, dominant source
- code evidence: file, function, guard condition, retry path, error mapping, or logging call

Read [references/remediation-playbook.md](references/remediation-playbook.md) when you need heuristics for likely fixes or log-hygiene improvements.

## Output Shape

Return a report with these sections:

1. Scope: analyzed path, number of sources, total events, and unsupported inputs if any
2. Top repeated logs: count, severity mix, sample, likely code location
3. Exception summary: type, count, sample stack or message, likely origin
4. Recommendations: concrete fixes, logging improvements, and validation or monitoring suggestions
5. Confidence and gaps: say where a code match is inferred rather than exact

## Guardrails

- Do not guess code locations without showing the search trail.
- Call out unsupported archive formats instead of silently ignoring them.
- Prefer the current workspace as the code repository unless the user points to a different one.
- If logs contain secrets, summarize them without echoing full tokens, passwords, or long identifiers.
- If the log volume is huge, keep the script output as the primary artifact and inspect only the highest-signal patterns.

## Examples

- `Use $log-analyzer on /tmp/case-184/logs and tell me which errors are most frequent.`
- `Use $log-analyzer to inspect ~/Downloads/support-bundle and map the top exceptions back to this repo.`
- `Use $log-analyzer on a zipped production log package, summarize noisy logs, and recommend code changes.`
