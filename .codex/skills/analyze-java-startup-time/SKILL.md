---
name: analyze-java-startup-time
description: Analyze Java microservice startup and restart-to-available latency, including Java 微服务启动耗时分析 and 重启到可用耗时拆解. Use when Codex needs to inspect Spring Boot, JVM, Kubernetes/container events, application logs, APM traces, readiness/liveness probes, service discovery, or deployment evidence to explain where startup time or restart recovery time is spent and recommend targeted fixes.
---

# Analyze Java Startup Time

## Overview

Use this skill to produce an evidence-backed breakdown of Java microservice startup time, including cold startup and restart-to-available recovery. Treat "available" as the first externally useful signal, not merely "process started".

## Workflow

1. Define the timing question.
   - For startup: measure from process/container start to the chosen availability signal.
   - For restart-to-available: include shutdown/drain, scheduler/container delay, process/JVM boot, app initialization, readiness, and traffic routing.
   - If the user does not define "available", choose the strongest signal present: readiness accepting traffic, first successful health check, first 2xx business request, service registry visible, then port listening. State the confidence.

2. Collect evidence before diagnosing.
   - Application stdout/stderr logs from before process start through availability.
   - Previous-instance logs for restarts, such as `kubectl logs --previous`.
   - Kubernetes `describe pod`, events, deployment/rollout history, probe config, container start/finish times, and restart count when available.
   - JVM flags, Spring Boot version, image/deployment timestamps, APM spans, service mesh/gateway logs, registry/config-center logs, and health endpoint samples when relevant.

3. Extract a first-pass timeline with the bundled script:

   ```bash
   python3 <skill-dir>/scripts/extract_startup_timeline.py <log-file-or-dir> --format markdown --out /tmp/java-startup-timeline.md
   ```

   Use `--format json` when another tool or spreadsheet will consume the output. The script is heuristic; use it to find anchors and suspicious gaps, then verify against raw artifacts.

4. Build the critical-path timeline.
   - Anchor candidate events: restart requested, old instance unready, shutdown begin, container created, process first log, Spring application starting, environment/config loaded, context refresh, dependency connection, migrations done, embedded server listening, warmup complete, service registered, readiness accepting traffic, first successful request.
   - Separate wall-clock gaps from reported framework durations. Spring Boot's `Started ... in X seconds` usually excludes platform scheduling, image pull, preStop drain, readiness probe delay, and traffic routing propagation.
   - Normalize time zones and note clock skew, missing dates, interleaved files, and multiline stack traces.

5. Attribute elapsed time by phase.
   - Platform/restart overhead: deployment decision, old pod drain, scheduling, image pull, container creation, restart backoff.
   - JVM/process boot: JVM creation, agent loading, classpath scan, logging initialization.
   - Configuration and discovery: config server, Nacos/Apollo/Consul/Eureka, DNS, TLS, metadata calls.
   - Spring context and beans: auto-configuration, component scanning, bean creation, proxy/AOP, validation.
   - Dependencies: DB connection pool, ORM metadata, Redis, MQ, Elasticsearch, downstream health checks.
   - Data changes: Flyway/Liquibase migrations, schema validation, seed data, lock contention.
   - Runtime availability: web server bind/listen, cache warmup, readiness health indicators, probe delay/failures, registry/gateway propagation.

6. Deliver a concise diagnosis.
   - Start with total elapsed time and the largest contributors.
   - Include a table with phase, start/end markers, elapsed time, evidence, and confidence.
   - Identify the critical path separately from parallel/background work.
   - Call out missing evidence and whether each conclusion is exact, inferred, or speculative.
   - Recommend fixes ranked by likely impact and verification method.

## Reference

Read `references/startup-phase-map.md` when you need marker patterns, phase definitions, common root causes, or a structured restart-to-available model.

## Guardrails

- Do not treat "port listening" as fully available when readiness, registry, gateway, or first-request evidence says otherwise.
- Do not blame slow beans, DB migrations, config centers, or probes without timestamp evidence or a clearly labeled inference.
- Prefer absolute timestamps and elapsed wall time over log order alone.
- If logs only cover the Java process, explicitly say that platform and routing overhead are outside the observed window.
