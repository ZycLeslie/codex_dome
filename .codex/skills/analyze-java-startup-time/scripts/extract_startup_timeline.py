#!/usr/bin/env python3
"""Extract startup/restart timeline hints from Java microservice logs."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TIMESTAMP_PATTERNS = [
    re.compile(
        r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,9})?(?:Z|[+-]\d{2}:?\d{2})?)"
    ),
    re.compile(
        r"(?P<ts>\d{4}/\d{2}/\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,9})?)"
    ),
    re.compile(r"(?P<ts>\d{2}:\d{2}:\d{2}(?:[.,]\d{1,9})?)"),
]


EVENT_PATTERNS = [
    ("shutdown", "Shutdown or termination began", 0.82, re.compile(r"\b(SIGTERM|Shutdown|shutting down|Graceful shutdown|Stopping service|ContextClosedEvent)\b", re.I)),
    ("jvm-process", "JVM/process log observed", 0.65, re.compile(r"\b(JAVA_TOOL_OPTIONS|Picked up _JAVA_OPTIONS|OpenJDK|VM settings|JVM|Java HotSpot)\b", re.I)),
    ("spring-start", "Spring application starting", 0.95, re.compile(r"\bStarting .*(using Java|with PID)\b|\bSpringApplication\b", re.I)),
    ("profile-config", "Profiles or configuration loading", 0.82, re.compile(r"\b(No active profile set|profiles? are active|Fetching config|Located property source|Config Server|Nacos|Apollo|bootstrap context)\b", re.I)),
    ("context-refresh", "Spring context initialization", 0.78, re.compile(r"\b(Root WebApplicationContext|Refreshing .*ApplicationContext|BeanFactory|context initialization completed)\b", re.I)),
    ("dependency-db", "Database/persistence initialization", 0.84, re.compile(r"\b(HikariPool|EntityManagerFactory|Hibernate|JPA|JDBC|DataSource)\b", re.I)),
    ("migration", "Database migration", 0.9, re.compile(r"\b(Flyway|Liquibase|Migrating schema|Successfully applied|ChangeSet|database migration)\b", re.I)),
    ("embedded-server", "Embedded server initialized/listening", 0.9, re.compile(r"\b(Tomcat initialized|Tomcat started|Netty started|Undertow started|Jetty started|Started ServerConnector|gRPC Server started|listening on port|started on port)\b", re.I)),
    ("warmup", "Warmup/preload/cache work", 0.72, re.compile(r"\b(warm-?up|preload|pre-loading|prime cache|loading cache|dictionary|initializing cache)\b", re.I)),
    ("discovery", "Service discovery or registration", 0.78, re.compile(r"\b(Eureka|Consul|ServiceRegistry|service registered|Registered instance|registration status|Nacos Naming)\b", re.I)),
    ("readiness", "Readiness accepting traffic", 0.96, re.compile(r"\b(ReadinessState.*ACCEPTING_TRAFFIC|readiness.*(UP|success|succeeded)|Started .*Health|Application is ready|accepting traffic)\b", re.I)),
    ("probe-failed", "Readiness/liveness probe failed", 0.9, re.compile(r"\b(Readiness probe failed|Liveness probe failed|health check failed|readiness.*DOWN)\b", re.I)),
    ("app-started", "Spring application reported started", 0.95, re.compile(r"\bStarted .* in (?P<seconds>\d+(?:\.\d+)?) seconds\b", re.I)),
    ("traffic", "Successful traffic observed", 0.86, re.compile(r"\b(HTTP/[0-9.]+\"?\s+2\d\d|status[=: ]2\d\d|completed.*2\d\d|request.*success)\b", re.I)),
]


@dataclass
class Event:
    ts: str
    epoch_ms: int
    category: str
    label: str
    confidence: float
    file: str
    line: int
    message: str
    reported_duration_seconds: float | None = None


def parse_timestamp(line: str, current_date: datetime | None) -> tuple[datetime | None, datetime | None]:
    for index, pattern in enumerate(TIMESTAMP_PATTERNS):
        match = pattern.search(line)
        if not match:
            continue
        raw = match.group("ts").replace(",", ".")
        try:
            if index == 0:
                normalized = raw.replace("Z", "+00:00")
                if "." in normalized:
                    normalized = trim_fraction(normalized)
                dt = datetime.fromisoformat(normalized)
            elif index == 1:
                normalized = trim_fraction(raw.replace("/", "-"))
                dt = datetime.fromisoformat(normalized)
            else:
                if current_date is None:
                    return None, current_date
                time_part = trim_fraction(raw)
                parsed_time = datetime.strptime(time_part, "%H:%M:%S.%f" if "." in time_part else "%H:%M:%S").time()
                dt = datetime.combine(current_date.date(), parsed_time, tzinfo=current_date.tzinfo)
            return dt, dt
        except ValueError:
            continue
    return None, current_date


def trim_fraction(value: str) -> str:
    return re.sub(r"\.(\d{6})\d+", r".\1", value)


def epoch_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def isoformat(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat(sep=" ")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def discover_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and not is_ignored(child):
                    files.append(child)
        elif path.is_file():
            files.append(path)
    return files


def is_ignored(path: Path) -> bool:
    ignored_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".jar", ".war", ".class", ".zip"}
    return any(str(path).lower().endswith(suffix) for suffix in ignored_suffixes)


def iter_lines(path: Path) -> Iterable[tuple[int, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    mode = "rt"
    try:
        with opener(path, mode, encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                yield line_number, line.rstrip("\n")
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)


def classify(line: str) -> tuple[str, str, float, float | None] | None:
    for category, label, confidence, pattern in EVENT_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        duration = None
        if "seconds" in match.groupdict() and match.group("seconds"):
            duration = float(match.group("seconds"))
        return category, label, confidence, duration
    return None


def extract_events(files: list[Path]) -> list[Event]:
    events: list[Event] = []
    for path in files:
        current_date: datetime | None = None
        first_logged_event_added = False
        for line_number, line in iter_lines(path):
            dt, current_date = parse_timestamp(line, current_date)
            if dt is None:
                continue
            if not first_logged_event_added:
                events.append(
                    Event(
                        ts=isoformat(dt),
                        epoch_ms=epoch_ms(dt),
                        category="log-start",
                        label="First timestamped log line in file",
                        confidence=0.55,
                        file=str(path),
                        line=line_number,
                        message=compact(line),
                    )
                )
                first_logged_event_added = True
            classified = classify(line)
            if classified is None:
                continue
            category, label, confidence, duration = classified
            events.append(
                Event(
                    ts=isoformat(dt),
                    epoch_ms=epoch_ms(dt),
                    category=category,
                    label=label,
                    confidence=confidence,
                    file=str(path),
                    line=line_number,
                    message=compact(line),
                    reported_duration_seconds=duration,
                )
            )
    return sorted(events, key=lambda event: (event.epoch_ms, event.file, event.line))


def compact(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def first(events: list[Event], *categories: str) -> Event | None:
    category_set = set(categories)
    return next((event for event in events if event.category in category_set), None)


def first_after(events: list[Event], categories: Iterable[str], after: Event | None) -> Event | None:
    category_set = set(categories)
    minimum_epoch = after.epoch_ms if after is not None else None
    return next(
        (
            event
            for event in events
            if event.category in category_set and (minimum_epoch is None or event.epoch_ms >= minimum_epoch)
        ),
        None,
    )


def duration_seconds(start: Event | None, end: Event | None) -> float | None:
    if start is None or end is None:
        return None
    delta = round((end.epoch_ms - start.epoch_ms) / 1000.0, 3)
    return delta if delta >= 0 else None


def summarize(events: list[Event]) -> dict[str, object]:
    shutdown = first(events, "shutdown")
    process_start = first_after(events, ["jvm-process", "log-start"], shutdown) or first(events, "jvm-process", "log-start")
    spring_start = first_after(events, ["spring-start"], shutdown) or first(events, "spring-start")
    if (
        process_start is None
        or (spring_start is not None and process_start.epoch_ms > spring_start.epoch_ms)
        or (shutdown is not None and spring_start is not None and process_start.epoch_ms < shutdown.epoch_ms)
    ):
        process_start = spring_start
    server = first_after(events, ["embedded-server"], spring_start or process_start)
    app_started = first_after(events, ["app-started"], spring_start or process_start)
    readiness = first_after(events, ["readiness", "traffic"], spring_start or process_start)
    available = readiness or app_started or server
    return {
        "event_count": len(events),
        "anchors": {
            "process_or_log_start": asdict(process_start) if process_start else None,
            "shutdown_begin": asdict(shutdown) if shutdown else None,
            "spring_start": asdict(spring_start) if spring_start else None,
            "server_listening": asdict(server) if server else None,
            "app_started": asdict(app_started) if app_started else None,
            "available_marker": asdict(available) if available else None,
        },
        "durations_seconds": {
            "process_or_log_start_to_spring_start": duration_seconds(process_start, spring_start),
            "spring_start_to_server_listening": duration_seconds(spring_start, server),
            "spring_start_to_app_started": duration_seconds(spring_start, app_started),
            "process_or_log_start_to_available": duration_seconds(process_start, available),
            "shutdown_begin_to_available": duration_seconds(shutdown, available),
        },
        "reported_spring_boot_seconds": next((event.reported_duration_seconds for event in events if event.reported_duration_seconds is not None), None),
    }


def gaps(events: list[Event], limit: int) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for left, right in zip(events, events[1:]):
        delta = round((right.epoch_ms - left.epoch_ms) / 1000.0, 3)
        if delta <= 0:
            continue
        pairs.append(
            {
                "seconds": delta,
                "from": asdict(left),
                "to": asdict(right),
            }
        )
    return sorted(pairs, key=lambda item: item["seconds"], reverse=True)[:limit]


def render_markdown(events: list[Event], summary: dict[str, object], gap_rows: list[dict[str, object]]) -> str:
    lines = ["# Java Startup Timeline", ""]
    lines.append(f"- Matched events: {len(events)}")
    reported = summary["reported_spring_boot_seconds"]
    if reported is not None:
        lines.append(f"- Spring reported startup: {reported} seconds")
    for name, value in summary["durations_seconds"].items():
        if value is not None:
            lines.append(f"- {name}: {value} seconds")
    lines.append("")
    lines.append("## Timeline")
    lines.append("")
    lines.append("| Time | +Prev | +First | Category | Evidence | Source |")
    lines.append("| --- | ---: | ---: | --- | --- | --- |")
    first_epoch = events[0].epoch_ms if events else 0
    previous_epoch = first_epoch
    for event in events:
        delta_prev = round((event.epoch_ms - previous_epoch) / 1000.0, 3)
        delta_first = round((event.epoch_ms - first_epoch) / 1000.0, 3)
        source = f"{Path(event.file).name}:{event.line}"
        lines.append(
            f"| {escape(event.ts)} | {delta_prev} | {delta_first} | {event.category} | {escape(event.message)} | {escape(source)} |"
        )
        previous_epoch = event.epoch_ms
    lines.append("")
    lines.append("## Largest Gaps Between Matched Events")
    lines.append("")
    if not gap_rows:
        lines.append("No positive gaps detected between matched events.")
    else:
        lines.append("| Seconds | From | To |")
        lines.append("| ---: | --- | --- |")
        for gap in gap_rows:
            left = gap["from"]
            right = gap["to"]
            lines.append(
                f"| {gap['seconds']} | {escape(left['category'] + ' ' + left['ts'])} | {escape(right['category'] + ' ' + right['ts'])} |"
            )
    lines.append("")
    lines.append("Use this as a lead list. Verify phase boundaries against raw logs before making claims.")
    return "\n".join(lines) + "\n"


def escape(value: str) -> str:
    return value.replace("|", "\\|")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Log files or directories to scan. .gz files are supported.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Write output to a file instead of stdout.")
    parser.add_argument("--top-gaps", type=int, default=8, help="Number of largest gaps to report.")
    args = parser.parse_args()

    files = discover_files(args.inputs)
    if not files:
        print("No readable input files found.", file=sys.stderr)
        return 2

    events = extract_events(files)
    if not events:
        print("No timestamped startup-related events found.", file=sys.stderr)
        return 1

    summary = summarize(events)
    gap_rows = gaps(events, args.top_gaps)
    if args.format == "json":
        output = json.dumps(
            {
                "summary": summary,
                "gaps": gap_rows,
                "events": [asdict(event) for event in events],
            },
            indent=2,
            ensure_ascii=False,
        )
    else:
        output = render_markdown(events, summary, gap_rows)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
