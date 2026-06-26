# JVM Runtime Monitoring Playbook

## Target Setup

Capture a target contract before executing commands:

| Field | Examples |
| --- | --- |
| Environment | `local`, `vm`, `docker`, `kubernetes` |
| Locator | PID `1234`, SSH host `app-prod-1`, Docker container `order-api`, namespace/pod/container |
| Selector | main class, jar name, command-line pattern, service label |
| Window | interval `5s`, duration `10m`, output dir `/tmp/jvm-monitor-...` |
| Tools | Actuator/Micrometer, `jcmd/jstat`, `arthas`, `visualvm/jmx`, `jfr` |
| Safety | prod/non-prod, attach allowed, heap dump allowed, JFR allowed |

## Environment Command Patterns

### Local

```bash
jcmd -l || jps -lv || ps -ef | grep '[j]ava'
PID=<pid>
mkdir -p /tmp/jvm-monitor
jcmd "$PID" VM.version > /tmp/jvm-monitor/vm-version.txt
jcmd "$PID" VM.command_line > /tmp/jvm-monitor/vm-command-line.txt
jcmd "$PID" VM.flags > /tmp/jvm-monitor/vm-flags.txt
jcmd "$PID" GC.heap_info > /tmp/jvm-monitor/heap-info.txt
jstat -gcutil "$PID" 5000 120 > /tmp/jvm-monitor/jstat-gcutil.tsv
```

### VM Over SSH

Prefer an existing SSH alias or bastion-approved command. Keep output on the target first, then copy artifacts back.

```bash
ssh <host> 'jcmd -l || jps -lv || ps -ef | grep '"'"'[j]ava'"'"''
ssh <host> 'PID=<pid>; OUT=/tmp/jvm-monitor; mkdir -p "$OUT"; jstat -gcutil "$PID" 5000 120 > "$OUT/jstat-gcutil.tsv"'
scp -r <host>:/tmp/jvm-monitor ./jvm-monitor-<host>
```

### Docker Container

```bash
docker exec <container> sh -lc 'jcmd -l || jps -lv || ps -ef | grep "[j]ava"'
docker exec <container> sh -lc 'PID=<pid>; OUT=/tmp/jvm-monitor; mkdir -p "$OUT"; jcmd "$PID" VM.flags > "$OUT/vm-flags.txt"; jstat -gcutil "$PID" 5000 120 > "$OUT/jstat-gcutil.tsv"'
docker cp <container>:/tmp/jvm-monitor ./jvm-monitor-<container>
```

If the container lacks JDK tools, try host-side container metrics, application metrics endpoints, JMX port-forwarding, or Arthas attach when allowed.

### Kubernetes

```bash
kubectl -n <namespace> exec <pod> -c <container> -- sh -lc 'jcmd -l || jps -lv || ps -ef | grep "[j]ava"'
kubectl -n <namespace> exec <pod> -c <container> -- sh -lc 'PID=<pid>; OUT=/tmp/jvm-monitor; mkdir -p "$OUT"; jstat -gcutil "$PID" 5000 120 > "$OUT/jstat-gcutil.tsv"'
kubectl -n <namespace> cp <pod>:/tmp/jvm-monitor ./jvm-monitor-<pod> -c <container>
```

Use `kubectl top pod`, pod limits/requests, restart count, OOMKilled status, and recent events to explain JVM metrics inside the container boundary.

## Recommended Spring Boot Actuator Baseline

Use Spring Boot Actuator as the recommended first layer for Spring Boot services. It is remote-friendly, scriptable over HTTP, and easy to feed into Prometheus or an existing observability stack. Use JVM attach tools when Actuator does not expose enough detail or when you need owner paths, lock owners, native memory, JFR, or method-level profiling.

### Suggested Dependencies

Maven:

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

Gradle:

```gradle
implementation "org.springframework.boot:spring-boot-starter-actuator"
runtimeOnly "io.micrometer:micrometer-registry-prometheus"
```

### Recommended Exposure

Start with read-only, low-risk endpoints:

```properties
management.endpoints.web.exposure.include=health,info,metrics,prometheus,threaddump
management.endpoint.health.show-details=when-authorized
management.server.port=8081
```

Only expose endpoints through a private network, gateway, service mesh policy, SSH tunnel, or Kubernetes port-forward. Secure them with Spring Security, platform auth, or an equivalent control. Avoid exposing `env`, `configprops`, `logfile`, `heapdump`, `shutdown`, and logger mutation endpoints except for tightly controlled administrator workflows.

### Useful Endpoints

```bash
ACTUATOR=${ACTUATOR_BASE_URL:-http://127.0.0.1:8080/actuator}
curl -fsS "$ACTUATOR/health"
curl -fsS "$ACTUATOR/info"
curl -fsS "$ACTUATOR/metrics"
curl -fsS "$ACTUATOR/metrics/jvm.memory.used"
curl -fsS "$ACTUATOR/metrics/jvm.memory.max"
curl -fsS "$ACTUATOR/metrics/jvm.gc.pause"
curl -fsS "$ACTUATOR/metrics/jvm.threads.live"
curl -fsS "$ACTUATOR/metrics/process.cpu.usage"
curl -fsS "$ACTUATOR/metrics/system.cpu.usage"
curl -fsS "$ACTUATOR/prometheus"
curl -fsS "$ACTUATOR/threaddump"
```

When authentication is required, prefer an environment variable rather than embedding credentials in command history:

```bash
ACTUATOR_AUTH_HEADER='Authorization: Bearer <token>'
curl -fsS -H "$ACTUATOR_AUTH_HEADER" "$ACTUATOR/metrics/jvm.memory.used"
```

### Actuator Interpretation

| Endpoint or metric | Use |
| --- | --- |
| `health` | Check dependency health, readiness-like state, and component degradation |
| `metrics/jvm.memory.used` and `metrics/jvm.memory.max` | Track heap, non-heap, and memory-pool pressure |
| `metrics/jvm.gc.pause` | Detect GC pause frequency and latency impact |
| `metrics/jvm.threads.live` | Watch thread growth and compare with thread dumps |
| `metrics/process.cpu.usage` | Identify process CPU pressure before attaching profilers |
| `prometheus` | Feed Prometheus/Grafana and scheduled reports |
| `threaddump` | Capture thread evidence without shelling into the host |

Treat Actuator as telemetry, not proof of object ownership. Use heap dumps, MAT, JFR allocation events, thread dumps, or Arthas/JMX when the report needs root-cause evidence.

## Tool Selection

### jcmd and jstat

Use these first when available because they are low overhead and scriptable.

Useful commands:

```bash
jcmd "$PID" VM.version
jcmd "$PID" VM.command_line
jcmd "$PID" VM.flags
jcmd "$PID" GC.heap_info
jcmd "$PID" Thread.print -l
jcmd "$PID" VM.native_memory summary
jstat -gcutil "$PID" <interval-ms> <count>
jstat -gccapacity "$PID" <interval-ms> <count>
```

`VM.native_memory summary` only works when Native Memory Tracking was enabled, usually with `-XX:NativeMemoryTracking=summary` or `detail`.

### Arthas

Use Arthas for live triage after approval to attach an agent.

Common interactive commands:

```text
dashboard -i 5000 -n 12
jvm
memory
thread -n 20
thread --state BLOCKED
heapdump --live /tmp/heap-live.hprof
profiler start
profiler stop --format html
```

Use `heapdump`, `profiler`, `trace`, `watch`, and `tt` carefully in production. They can expose sensitive data or create overhead. Prefer `dashboard`, `jvm`, `memory`, and `thread` for first response.

### VisualVM and JMX

Use VisualVM when the user wants GUI charts, sampler views, MBeans, or manual inspection. For remote JVMs, prefer a tunnel instead of exposing JMX directly.

Local attach:

```bash
visualvm
```

Start a temporary local JMX management agent only when approved:

```bash
jcmd "$PID" ManagementAgent.start jmxremote.port=9010 jmxremote.authenticate=false jmxremote.ssl=false
```

SSH tunnel for a VM:

```bash
ssh -L 9010:127.0.0.1:9010 <host>
```

Kubernetes port-forward:

```bash
kubectl -n <namespace> port-forward <pod> 9010:9010
```

For RMI-based JMX, `jmxremote.rmi.port` and `java.rmi.server.hostname` may need to be configured at JVM startup. Avoid unauthenticated JMX outside a trusted tunnel.

### JFR

Use JFR for bounded profiling windows:

```bash
jcmd "$PID" JFR.start name=codex-monitor settings=profile delay=0s duration=300s filename=/tmp/jvm-monitor/runtime.jfr
jcmd "$PID" JFR.check name=codex-monitor
jcmd "$PID" JFR.dump name=codex-monitor filename=/tmp/jvm-monitor/runtime.jfr
```

JFR is usually lower overhead than ad hoc profilers, but still requires approval in production.

## Scheduled Monitoring Patterns

### Bounded Shell Loop

```bash
PID=<pid>
OUT=/tmp/jvm-monitor
INTERVAL=10
DURATION=600
mkdir -p "$OUT"
end=$((SECONDS + DURATION))
while [ "$SECONDS" -lt "$end" ]; do
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  jcmd "$PID" GC.heap_info > "$OUT/heap-$ts.txt" 2>&1
  jcmd "$PID" Thread.print -l > "$OUT/thread-$ts.txt" 2>&1
  jcmd "$PID" VM.native_memory summary > "$OUT/nmt-$ts.txt" 2>&1 || true
  jstat -gcutil "$PID" 1000 1 >> "$OUT/jstat-gcutil.tsv" 2>&1
  sleep "$INTERVAL"
done
```

### Cron or systemd Timer

Use for recurring checks when the environment owner approves persistent monitoring. Keep scripts idempotent, rotate artifacts, and cap disk usage.

### Kubernetes CronJob

Use a CronJob only when the cluster allows exec or sidecar-based collection. Prefer existing metrics stacks if Prometheus, JMX exporter, Micrometer, or APM is already present.

## Interpretation Guide

| Signal | Possible meaning | Caveat |
| --- | --- | --- |
| Old gen `O` stays high and full GC count rises | Heap pressure or leak candidate | Need trend and object ownership evidence |
| `FGC` increases during latency spike | Stop-the-world pressure | Correlate with GC logs and application latency |
| Metaspace `M` keeps rising | Classloader/proxy leak or normal dynamic loading | Verify class count and redeploy behavior |
| Thread count grows, many WAITING/TIMED_WAITING | Pool growth, blocked consumers, scheduler buildup | Thread dumps need name and stack grouping |
| Many BLOCKED threads | Lock contention | Identify owner thread and monitor object |
| Container RSS near limit, heap not full | Native/off-heap, direct buffers, threads, mmap, allocator | Check NMT, cgroup memory, direct memory flags |
| High CPU with low GC | Application hot code, locks, serialization, crypto, regex | Use JFR, async-profiler, or Arthas profiler if approved |
| Frequent young GC, low old gen | Allocation churn | Use JFR allocation events or allocation profiler |

## Report Template

Return a report with:

1. Target: environment, locator, PID/selector, JVM version, container or VM limits.
2. Window: start/end time, interval, duration, commands/tools, files collected.
3. Health summary: heap, metaspace, GC counts/time, thread states, CPU/memory boundary, JFR/Arthas observations.
4. Evidence table: metric, value or delta, artifact, timestamp, interpretation, confidence.
5. Findings: what is currently healthy, degraded, or risky.
6. Likely causes: explain only when evidence supports it; otherwise state the next evidence needed.
7. Recommendations: immediate mitigation, deeper capture plan, code/config follow-up, and monitoring to keep.
8. Gaps and risks: missing tools, single snapshot, clock skew, production overhead, missing container limits, redacted sensitive data.
