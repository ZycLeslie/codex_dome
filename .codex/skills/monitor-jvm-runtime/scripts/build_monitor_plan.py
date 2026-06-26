#!/usr/bin/env python3
"""Build a reviewable JVM runtime monitoring command plan."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
from dataclasses import dataclass, asdict


@dataclass
class Step:
    title: str
    commands: list[str]
    notes: list[str]


def parse_duration(value: str) -> int:
    match = re.fullmatch(r"\s*(\d+)\s*([smh]?)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid duration: {value}")
    amount = int(match.group(1))
    unit = match.group(2) or "s"
    multiplier = {"s": 1, "m": 60, "h": 3600}[unit]
    return amount * multiplier


def quote(value: str) -> str:
    return shlex.quote(value)


def wrap_command(args: argparse.Namespace, inner: str) -> str:
    if args.environment == "local":
        return inner
    if args.environment == "vm":
        host = args.ssh_host or args.target or "<ssh-host>"
        return f"ssh {quote(host)} {quote(inner)}"
    if args.environment == "docker":
        container = args.container or args.target or "<container>"
        return f"docker exec {quote(container)} sh -lc {quote(inner)}"
    if args.environment == "kubernetes":
        namespace = args.namespace or "default"
        pod = args.pod or args.target or "<pod>"
        container_part = f" -c {quote(args.kube_container)}" if args.kube_container else ""
        return f"kubectl -n {quote(namespace)} exec {quote(pod)}{container_part} -- sh -lc {quote(inner)}"
    return inner


def pid_assignment(args: argparse.Namespace) -> str:
    if args.pid:
        return f"PID={quote(args.pid)}"
    pattern = args.process_match or "<main-class-or-jar-pattern>"
    awk = "NR>1 && $0 ~ pat {print $1; exit}"
    return f"PID=$(jcmd 2>/dev/null | awk -v pat={quote(pattern)} {quote(awk)})"


def pid_prefix(args: argparse.Namespace) -> str:
    return f"{pid_assignment(args)}; test -n \"$PID\" || {{ echo 'PID not found' >&2; exit 2; }}"


def sample_count(duration_s: int, interval_s: int) -> int:
    return max(1, int(math.ceil(duration_s / max(1, interval_s))))


def actuator_command(args: argparse.Namespace, duration_s: int, interval_s: int) -> str:
    base_url = args.actuator_base_url or "${ACTUATOR_BASE_URL:-http://127.0.0.1:8080/actuator}"
    auth = '"${ACTUATOR_AUTH_HEADER:+-H}" ${ACTUATOR_AUTH_HEADER:+"$ACTUATOR_AUTH_HEADER"}'
    endpoints = "health info metrics metrics/jvm.memory.used metrics/jvm.memory.max metrics/jvm.gc.pause metrics/jvm.threads.live metrics/process.cpu.usage metrics/system.cpu.usage prometheus threaddump"
    if args.mode == "realtime":
        return (
            f"ACTUATOR={quote(base_url)}; OUT={quote(args.out_dir)}; mkdir -p \"$OUT\"; "
            f"for endpoint in {endpoints}; do safe=$(printf '%s' \"$endpoint\" | tr '/.' '__'); "
            f"curl -fsS {auth} \"$ACTUATOR/$endpoint\" > \"$OUT/actuator-$safe.txt\" || true; done"
        )
    return (
        f"ACTUATOR={quote(base_url)}; OUT={quote(args.out_dir)}; INTERVAL={interval_s}; DURATION={duration_s}; "
        "mkdir -p \"$OUT\"; end=$((SECONDS + DURATION)); "
        "while [ \"$SECONDS\" -lt \"$end\" ]; do "
        "ts=$(date -u +%Y%m%dT%H%M%SZ); "
        f"for endpoint in {endpoints}; do safe=$(printf '%s' \"$endpoint\" | tr '/.' '__'); "
        f"curl -fsS {auth} \"$ACTUATOR/$endpoint\" > \"$OUT/actuator-$safe-$ts.txt\" || true; done; "
        "sleep \"$INTERVAL\"; "
        "done"
    )


def build_steps(args: argparse.Namespace) -> list[Step]:
    duration_s = parse_duration(args.duration)
    interval_s = parse_duration(args.interval)
    interval_ms = interval_s * 1000
    count = sample_count(duration_s, interval_s)
    out_dir = args.out_dir
    pid = pid_prefix(args)

    if args.mode == "report-only":
        return [
            Step(
                "Summarize existing artifacts",
                [
                    f"python3 <skill-dir>/scripts/summarize_monitor_data.py {quote(out_dir)} --format markdown --out {quote(out_dir.rstrip('/') + '-report.md')}"
                ],
                ["Use this mode when artifacts are already collected and no live connection should be attempted."],
            )
        ]

    steps: list[Step] = []

    if args.tool != "actuator":
        steps.extend(
            [
                Step(
                    "Discover JVM process",
                    [
                        wrap_command(args, "jcmd -l || jps -lv || ps -ef | grep '[j]ava'"),
                    ],
                    ["Verify the PID and command line before attaching tools."],
                ),
                Step(
                    "Collect baseline identity",
                    [
                        wrap_command(
                            args,
                            f"{pid}; OUT={quote(out_dir)}; mkdir -p \"$OUT\"; "
                            "date -u +%Y-%m-%dT%H:%M:%SZ > \"$OUT/collection-start.txt\"; "
                            "jcmd \"$PID\" VM.version > \"$OUT/vm-version.txt\" 2>&1; "
                            "jcmd \"$PID\" VM.command_line > \"$OUT/vm-command-line.txt\" 2>&1; "
                            "jcmd \"$PID\" VM.flags > \"$OUT/vm-flags.txt\" 2>&1; "
                            "jcmd \"$PID\" GC.heap_info > \"$OUT/heap-info.txt\" 2>&1",
                        )
                    ],
                    ["If jcmd is missing, use Arthas, JMX, application metrics, or host/container metrics."],
                ),
            ]
        )

    if args.mode in {"realtime", "scheduled"} and args.tool != "actuator":
        steps.append(
            Step(
                "Run low-overhead GC sampling",
                [
                    wrap_command(
                        args,
                        f"{pid}; OUT={quote(out_dir)}; mkdir -p \"$OUT\"; "
                        f"jstat -gcutil \"$PID\" {interval_ms} {count} > \"$OUT/jstat-gcutil.tsv\"",
                    )
                ],
                [f"Samples every {interval_s}s for about {duration_s}s."],
            )
        )

    if args.mode == "scheduled" and args.tool != "actuator":
        steps.append(
            Step(
                "Capture scheduled heap, thread, and native-memory snapshots",
                [
                    wrap_command(
                        args,
                        f"{pid}; OUT={quote(out_dir)}; INTERVAL={interval_s}; DURATION={duration_s}; "
                        "mkdir -p \"$OUT\"; end=$((SECONDS + DURATION)); "
                        "while [ \"$SECONDS\" -lt \"$end\" ]; do "
                        "ts=$(date -u +%Y%m%dT%H%M%SZ); "
                        "jcmd \"$PID\" GC.heap_info > \"$OUT/heap-$ts.txt\" 2>&1; "
                        "jcmd \"$PID\" Thread.print -l > \"$OUT/thread-$ts.txt\" 2>&1; "
                        "jcmd \"$PID\" VM.native_memory summary > \"$OUT/nmt-$ts.txt\" 2>&1 || true; "
                        "sleep \"$INTERVAL\"; "
                        "done",
                    )
                ],
                ["Native Memory Tracking output is available only when NMT was enabled before JVM start."],
            )
        )

    if args.tool in {"auto", "actuator"}:
        steps.append(
            Step(
                "Recommended Spring Boot Actuator sampling",
                [actuator_command(args, duration_s, interval_s)],
                [
                    "Recommended for Spring Boot services because it is remote-friendly and low intrusion.",
                    "Use a local, private, or port-forwarded Actuator URL; do not expose sensitive endpoints publicly.",
                    "Set ACTUATOR_AUTH_HEADER='Authorization: Bearer <token>' when authentication is required.",
                    "Prometheus output requires micrometer-registry-prometheus and the prometheus endpoint to be exposed.",
                ],
            )
        )

    if args.tool in {"auto", "arthas"}:
        steps.append(
            Step(
                "Optional Arthas live triage",
                [
                    wrap_command(
                        args,
                        f"{pid}; echo \"Attach Arthas to PID $PID, then run: dashboard -i {interval_ms} -n {count}; jvm; memory; thread -n 20\"",
                    )
                ],
                [
                    "Requires explicit approval to attach an agent.",
                    "Prefer dashboard, jvm, memory, and thread before profiler, trace, watch, tt, or heapdump.",
                ],
            )
        )

    if args.tool in {"auto", "visualvm", "jmx"}:
        steps.append(
            Step(
                "Optional VisualVM or JMX connection",
                [
                    wrap_command(
                        args,
                        f"{pid}; echo \"For a trusted tunnel, consider: jcmd $PID ManagementAgent.start "
                        "jmxremote.port=9010 jmxremote.authenticate=false jmxremote.ssl=false\"",
                    )
                ],
                [
                    "Do not expose unauthenticated JMX on an untrusted network.",
                    "For VMs use SSH port-forwarding; for Kubernetes use kubectl port-forward when approved.",
                ],
            )
        )

    if args.tool in {"auto", "jfr"} or args.include_jfr:
        steps.append(
            Step(
                "Optional bounded JFR capture",
                [
                    wrap_command(
                        args,
                        f"{pid}; OUT={quote(out_dir)}; mkdir -p \"$OUT\"; "
                        f"jcmd \"$PID\" JFR.start name=codex-monitor settings=profile duration={duration_s}s "
                        "filename=\"$OUT/runtime.jfr\"",
                    )
                ],
                ["Requires approval in production; use a bounded duration and record the expected overhead."],
            )
        )

    steps.append(
        Step(
            "Summarize artifacts",
            [
                f"python3 <skill-dir>/scripts/summarize_monitor_data.py {quote(out_dir)} --format markdown --out {quote(out_dir.rstrip('/') + '-report.md')}"
            ],
            ["Copy remote/container artifacts locally before running the summarizer, or run it where the files are stored."],
        )
    )
    return steps


def render_markdown(args: argparse.Namespace, steps: list[Step]) -> str:
    lines = [
        "# JVM Runtime Monitoring Plan",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Environment | `{args.environment}` |",
        f"| Mode | `{args.mode}` |",
        f"| Tool preference | `{args.tool}` |",
        f"| Duration | `{args.duration}` |",
        f"| Interval | `{args.interval}` |",
        f"| Output directory | `{args.out_dir}` |",
        "",
        "Review every command before execution, especially attach, JMX, JFR, heap dump, profiler, and sensitive Actuator endpoint actions.",
        "",
    ]
    for index, step in enumerate(steps, start=1):
        lines.extend([f"## {index}. {step.title}", ""])
        if step.notes:
            lines.extend(f"- {note}" for note in step.notes)
            lines.append("")
        for command in step.commands:
            lines.extend(["```bash", command, "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=["local", "vm", "docker", "kubernetes"], required=True)
    parser.add_argument("--target", help="Generic target locator: host, container, pod, or label")
    parser.add_argument("--pid", help="Known JVM PID")
    parser.add_argument("--process-match", help="Main class, jar, or command-line pattern used to find the PID")
    parser.add_argument("--ssh-host", help="VM SSH host or alias")
    parser.add_argument("--container", help="Docker container name or id")
    parser.add_argument("--namespace", help="Kubernetes namespace")
    parser.add_argument("--pod", help="Kubernetes pod name")
    parser.add_argument("--kube-container", help="Kubernetes container name")
    parser.add_argument("--mode", choices=["realtime", "scheduled", "report-only"], default="scheduled")
    parser.add_argument("--tool", choices=["auto", "jcmd", "jstat", "actuator", "arthas", "visualvm", "jmx", "jfr"], default="auto")
    parser.add_argument("--duration", default="10m", help="Sampling duration such as 60s, 10m, or 1h")
    parser.add_argument("--interval", default="10s", help="Sampling interval such as 5s or 1m")
    parser.add_argument("--out-dir", default="/tmp/jvm-monitor", help="Output directory on the target")
    parser.add_argument("--actuator-base-url", help="Spring Boot Actuator base URL, such as http://127.0.0.1:8080/actuator")
    parser.add_argument("--include-jfr", action="store_true", help="Include a bounded JFR command even when tool is not auto/jfr")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    steps = build_steps(args)
    if args.format == "json":
        print(json.dumps({"target": vars(args), "steps": [asdict(step) for step in steps]}, indent=2))
    else:
        print(render_markdown(args, steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
