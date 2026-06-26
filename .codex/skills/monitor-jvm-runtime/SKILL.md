---
name: monitor-jvm-runtime
description: Monitor live JVM runtime health and performance in local, VM, container, Kubernetes, or Spring Boot Actuator environments. Use when Codex needs to connect to a running JVM process with jcmd, jstat, Spring Boot Actuator, Micrometer/Prometheus, JMX, VisualVM, Arthas, or JFR; perform JVM 实时监控, 定时监控/巡检, GC/heap/thread/class/native-memory observation; or produce evidence-backed JVM runtime monitoring analysis reports.
---

# Monitor JVM Runtime

## Overview

Use this skill to connect to a running JVM in a specified environment, collect runtime evidence with low-risk tools, and turn live or scheduled samples into a concise monitoring report. Prefer commands that can be reviewed before execution and preserve raw artifacts for later diagnosis.

## Target Contract

Start by defining the target in a small contract. If the user omitted a field, infer it from local context when safe; otherwise ask only for the missing field that blocks connection.

- Environment: `local`, `vm`, `docker`, or `kubernetes`.
- Locator: host, SSH alias, container name, namespace/pod/container, or local PID.
- JVM selector: PID, main class, jar name, command-line pattern, service name, or Java user.
- Mode: `realtime`, `scheduled`, `report-only`, or a combination.
- Window: sampling interval, duration, and expected output directory.
- Tool preference: `auto`, `jcmd/jstat`, `actuator/prometheus`, `arthas`, `visualvm/jmx`, or `jfr`.
- Safety boundary: production or non-production, allowed overhead, whether heap dump, class histogram, JFR, or agent attach is permitted.

## Workflow

1. Build a monitoring plan before connecting.

   ```bash
   python3 <skill-dir>/scripts/build_monitor_plan.py \
     --environment docker \
     --container <container> \
     --process-match '<main-class-or-jar>' \
     --mode scheduled \
     --duration 10m \
     --interval 10s \
     --tool auto \
     --actuator-base-url http://127.0.0.1:8080/actuator \
     --out-dir /tmp/jvm-monitor
   ```

   Use `--format json` when another tool will execute or store the plan. Review generated SSH, `docker`, `kubectl`, `jcmd`, `jstat`, Spring Boot Actuator, Arthas, VisualVM/JMX, and JFR commands before running them.

2. Discover and verify the JVM process.

   Prefer `jcmd -l`, then `jps -lv`, then `ps -ef | grep '[j]ava'`. In containers, verify the JVM tools exist inside the target image; if only a JRE is present, prefer Arthas, JMX, or host-side `docker top`/`kubectl top` evidence.

3. Choose the lowest-risk tool that answers the question.

   - Use Spring Boot Actuator and Micrometer/Prometheus as the recommended baseline for Spring Boot services, especially for remote, containerized, or long-running scheduled monitoring.
   - Use `jstat` and `jcmd` for low-overhead GC, heap, thread, flags, class, and NMT snapshots.
   - Use Arthas for live console triage, dashboard, thread hot spots, method-level observation, and quick JVM inspection after explicit attach approval.
   - Use VisualVM/JMX when the user needs an interactive GUI, charts, MBeans, or remote observation through a secure tunnel.
   - Use JFR for scheduled profiling windows when allocation, locks, CPU, GC, or latency attribution matters and overhead is acceptable.

4. Collect raw artifacts.

   Keep raw command outputs in a timestamped directory: JVM identity, flags, heap info, `jstat -gcutil`, Actuator `health`/`metrics`/`prometheus`/`threaddump` output, thread dumps, top threads, NMT summary when enabled, Arthas dashboard snapshots, JMX/JFR exports, GC logs, and container or host CPU/memory samples.

5. Summarize collected data.

   ```bash
   python3 <skill-dir>/scripts/summarize_monitor_data.py /tmp/jvm-monitor \
     --format markdown \
     --out /tmp/jvm-monitor-report.md
   ```

   Treat the script output as a first pass. Verify suspicious conclusions against raw artifacts and the target's deployment context.

6. Deliver the monitoring report.

   Include target contract, collection window, tools used, metric tables, anomalies, likely causes, confidence, operational risk, and next monitoring actions. Separate observed facts from inferred explanations.

## Monitoring Modes

### Real-Time Monitoring

Use for active incidents or interactive diagnosis. Stream Actuator metrics or Prometheus output, `jstat`, Arthas `dashboard`, `thread -n`, GC/heap snapshots, host/container CPU and memory, and recent GC or application logs. Report current pressure, not long-term trends.

### Scheduled Monitoring

Use for periodic watch, regression checks, or "定时监控/巡检". Prefer Spring Boot Actuator/Micrometer metrics for the baseline, repeated low-overhead JVM snapshots for depth, and optional bounded JFR when profiling is needed. Store samples with timestamps so growth, GC frequency, full-GC deltas, thread-state drift, and container memory pressure can be compared over time.

### Report-Only Analysis

Use when the user already has monitoring artifacts. Run the summarizer, read raw files around every anomaly, and produce a report without attempting to reconnect.

## Reference

Read `references/jvm-runtime-monitoring-playbook.md` when you need environment-specific command recipes, VisualVM/JMX setup, Arthas usage, scheduled monitoring patterns, interpretation rules, or the report template.

## Guardrails

- Do not expose sensitive Spring Boot Actuator endpoints publicly. By default prefer `health`, `info`, `metrics`, and `prometheus`; keep `env`, `configprops`, `logfile`, `heapdump`, and mutating endpoints restricted to trusted administrators.
- Do not open unauthenticated JMX to an untrusted network. Use SSH port-forwarding, Kubernetes port-forwarding, or a private trusted network with authentication and TLS where possible.
- Do not download or inject Arthas, start JFR, trigger class histograms, run heap dumps, or enable management agents in production without explicit approval and an overhead/data-sensitivity warning.
- Do not assume PID `1` is the Java process in containers; verify with JVM tooling or process listing.
- Do not treat a single snapshot as a trend. Label single-point findings as current-state observations.
- Do not paste secrets, tokens, request payloads, or personal data from thread dumps, heap strings, system properties, or environment variables; redact and summarize.
- Prefer bounded durations and explicit output directories. Stop or clean up attach tools and tunnels when monitoring is complete.
