# Monitor JVM Runtime

`monitor-jvm-runtime` is a Codex skill for monitoring live JVM processes in local hosts, VMs, Docker containers, or Kubernetes pods. It helps prepare reviewable connection commands, collect low-risk runtime samples, and turn collected JVM evidence into a monitoring report.

## What It Supports

- Target environments: local machine, SSH VM, Docker container, Kubernetes pod/container.
- JVM discovery: PID, main class, jar name, process command pattern, service name, or Java user.
- Monitoring modes: real-time monitoring, scheduled sampling, and report-only analysis.
- Tooling: Spring Boot Actuator, Micrometer/Prometheus, `jcmd`, `jstat`, VisualVM/JMX, Arthas, and bounded JFR captures.
- Report evidence: Actuator `metrics`/`prometheus`/`threaddump`, GC utilization, heap/metaspace pressure, thread states, native memory markers, JFR files, Arthas snapshots, and container/host context.

## Skill Layout

```text
monitor-jvm-runtime/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/openai.yaml
├── references/jvm-runtime-monitoring-playbook.md
└── scripts/
    ├── build_monitor_plan.py
    └── summarize_monitor_data.py
```

## Quick Start

Generate a scheduled Docker monitoring plan:

```bash
python3 scripts/build_monitor_plan.py \
  --environment docker \
  --container order-api \
  --process-match order-service.jar \
  --mode scheduled \
  --duration 10m \
  --interval 10s \
  --tool auto \
  --actuator-base-url http://127.0.0.1:8080/actuator \
  --out-dir /tmp/jvm-monitor
```

Use Actuator as the recommended baseline for Spring Boot services:

```bash
python3 scripts/build_monitor_plan.py \
  --environment kubernetes \
  --namespace prod \
  --pod order-api-abc \
  --kube-container app \
  --mode scheduled \
  --duration 10m \
  --interval 10s \
  --tool actuator \
  --actuator-base-url http://127.0.0.1:8080/actuator \
  --out-dir /tmp/jvm-actuator-monitor
```

Generate a Kubernetes report-only plan for already collected artifacts:

```bash
python3 scripts/build_monitor_plan.py \
  --environment kubernetes \
  --namespace prod \
  --pod order-api-abc \
  --kube-container app \
  --mode report-only \
  --out-dir /tmp/jvm-monitor-existing
```

Summarize collected monitoring artifacts:

```bash
python3 scripts/summarize_monitor_data.py /tmp/jvm-monitor \
  --format markdown \
  --out /tmp/jvm-monitor-report.md
```

## Workflow

1. Define the target contract: environment, locator, JVM selector, mode, sampling window, tool preference, and safety boundary.
2. Generate a command plan with `build_monitor_plan.py`.
3. Review commands before execution, especially attach, JMX, JFR, profiler, class histogram, or heap dump actions.
4. Execute approved commands in the target environment.
5. Copy or preserve raw artifacts in a timestamped directory.
6. Run `summarize_monitor_data.py` and verify every anomaly against raw evidence.
7. Produce a report with target, window, tools, metrics, findings, risks, and next checks.

## Recommended Spring Boot Actuator Setup

For Spring Boot services, install Actuator and Prometheus registry when long-running remote monitoring is needed:

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

Start with a small secured endpoint set:

```properties
management.endpoints.web.exposure.include=health,info,metrics,prometheus,threaddump
management.endpoint.health.show-details=when-authorized
management.server.port=8081
```

Useful endpoints include `/actuator/health`, `/actuator/info`, `/actuator/metrics`, `/actuator/metrics/jvm.memory.used`, `/actuator/metrics/jvm.gc.pause`, `/actuator/metrics/jvm.threads.live`, `/actuator/prometheus`, and `/actuator/threaddump`.

## Safety Notes

- Do not expose unauthenticated JMX on untrusted networks.
- Do not expose sensitive Actuator endpoints publicly. Keep `env`, `configprops`, `logfile`, `heapdump`, `shutdown`, and mutating endpoints restricted to trusted administrators.
- Get explicit approval before attaching Arthas, starting JFR, enabling management agents, triggering class histograms, or taking heap dumps in production.
- Treat single snapshots as current-state observations, not trends.
- Redact secrets, tokens, request payloads, and personal data from thread dumps, system properties, heap strings, and environment output.
- Stop or clean up attach tools, tunnels, and temporary monitoring files after the session.

## More Detail

See `references/jvm-runtime-monitoring-playbook.md` for environment-specific command patterns, Arthas and VisualVM/JMX guidance, scheduled monitoring examples, interpretation rules, and the report template.
