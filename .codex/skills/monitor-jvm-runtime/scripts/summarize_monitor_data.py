#!/usr/bin/env python3
"""Summarize collected JVM runtime monitoring artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


PERCENT_COLUMNS = {"S0", "S1", "E", "O", "M", "CCS", "EU", "OU", "MU", "CCSU"}
COUNT_COLUMNS = {"YGC", "FGC", "CGC"}
TIME_COLUMNS = {"YGCT", "FGCT", "CGCT", "GCT"}


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(file for file in path.rglob("*") if file.is_file())


def to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_jstat_file(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    header: list[str] | None = None
    for raw_line in path.read_text(errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        if any(part in PERCENT_COLUMNS for part in parts) and any(part in COUNT_COLUMNS for part in parts):
            header = parts
            continue
        if not header:
            continue
        values = [to_float(part) for part in parts]
        if any(value is None for value in values):
            continue
        if len(values) != len(header):
            if len(values) == len(header) + 1 and header[0] != "Timestamp":
                header = ["Timestamp", *header]
            else:
                continue
        rows.append(dict(zip(header, values)))
    return rows


def summarize_jstat(files: list[Path]) -> dict:
    all_rows: list[dict[str, float]] = []
    source_files: list[str] = []
    for path in files:
        rows = parse_jstat_file(path)
        if rows:
            all_rows.extend(rows)
            source_files.append(str(path))
    summary: dict[str, object] = {"rows": len(all_rows), "files": source_files}
    if not all_rows:
        return summary

    columns = sorted({key for row in all_rows for key in row})
    percent_summary = {}
    for column in columns:
        values = [row[column] for row in all_rows if column in row]
        if column in PERCENT_COLUMNS and values:
            percent_summary[column] = {
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "avg": round(mean(values), 2),
                "last": round(values[-1], 2),
            }
    deltas = {}
    for column in sorted(COUNT_COLUMNS | TIME_COLUMNS):
        values = [row[column] for row in all_rows if column in row]
        if len(values) >= 2:
            deltas[column] = round(values[-1] - values[0], 3)
    summary["percent"] = percent_summary
    summary["deltas"] = deltas
    return summary


def parse_thread_states(files: list[Path]) -> dict:
    per_file = {}
    total = Counter()
    pattern = re.compile(r"java\.lang\.Thread\.State:\s+([A-Z_]+)")
    for path in files:
        text = path.read_text(errors="ignore")
        states = Counter(pattern.findall(text))
        if states:
            per_file[str(path)] = dict(states)
            total.update(states)
    return {"total": dict(total), "files": per_file}


def parse_heap_info(files: list[Path]) -> list[dict[str, str]]:
    snippets = []
    wanted = re.compile(r"(garbage-first heap|tenured generation|new generation|Metaspace|class space|used\s+\d+K|committed\s+\d+K)", re.I)
    for path in files:
        matches = [line.strip() for line in path.read_text(errors="ignore").splitlines() if wanted.search(line)]
        if matches:
            snippets.append({"file": str(path), "markers": matches[:12]})
    return snippets


def parse_nmt(files: list[Path]) -> list[dict[str, str]]:
    snippets = []
    wanted = re.compile(r"(Total:|Java Heap|Class|Thread|Code|GC|Internal|Symbol|Native Memory Tracking)", re.I)
    for path in files:
        matches = [line.strip() for line in path.read_text(errors="ignore").splitlines() if wanted.search(line)]
        if matches:
            snippets.append({"file": str(path), "markers": matches[:16]})
    return snippets


def classify_files(files: list[Path]) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        lower = path.name.lower()
        if "actuator" in lower:
            groups["actuator"].append(path)
        if "prometheus" in lower or lower.endswith(".prom"):
            groups["prometheus"].append(path)
        if "jstat" in lower or "gcutil" in lower or "gccapacity" in lower:
            groups["jstat"].append(path)
        if "thread" in lower or "threaddump" in lower:
            groups["thread"].append(path)
        if "heap" in lower:
            groups["heap"].append(path)
        if "nmt" in lower or "native" in lower:
            groups["nmt"].append(path)
        if lower.endswith(".jfr"):
            groups["jfr"].append(path)
        if "dashboard" in lower or "arthas" in lower:
            groups["arthas"].append(path)
    return groups


def build_findings(summary: dict) -> list[str]:
    findings = []
    jstat = summary.get("jstat", {})
    percent = jstat.get("percent", {}) if isinstance(jstat, dict) else {}
    deltas = jstat.get("deltas", {}) if isinstance(jstat, dict) else {}

    old = percent.get("O") or percent.get("OU")
    if old and old.get("max", 0) >= 85:
        findings.append(f"Old generation reached {old['max']}%; check for sustained heap pressure or leak evidence.")
    meta = percent.get("M") or percent.get("MU")
    if meta and meta.get("max", 0) >= 85:
        findings.append(f"Metaspace reached {meta['max']}%; inspect class loading and redeploy behavior.")
    if deltas.get("FGC", 0) > 0:
        findings.append(f"Full GC count increased by {deltas['FGC']}; correlate with pause time and latency.")
    if deltas.get("GCT", 0) > 0:
        findings.append(f"Total GC time increased by {deltas['GCT']}s during the sample window.")

    thread_total = summary.get("threads", {}).get("total", {})
    if thread_total.get("BLOCKED", 0) > 0:
        findings.append(f"Thread dumps include {thread_total['BLOCKED']} BLOCKED thread markers; inspect lock owners.")
    if not findings:
        findings.append("No high-confidence anomaly was detected by the summarizer; review raw artifacts for workload-specific issues.")
    return findings


def summarize(path: Path) -> dict:
    files = iter_files(path)
    groups = classify_files(files)
    summary = {
        "input": str(path),
        "file_count": len(files),
        "classified_files": {key: [str(item) for item in value] for key, value in groups.items()},
        "jstat": summarize_jstat(groups.get("jstat", [])),
        "threads": parse_thread_states(groups.get("thread", [])),
        "heap_markers": parse_heap_info(groups.get("heap", [])),
        "nmt_markers": parse_nmt(groups.get("nmt", [])),
        "actuator_files": [str(path) for path in groups.get("actuator", [])],
        "prometheus_files": [str(path) for path in groups.get("prometheus", [])],
        "jfr_files": [str(path) for path in groups.get("jfr", [])],
        "arthas_files": [str(path) for path in groups.get("arthas", [])],
    }
    summary["findings"] = build_findings(summary)
    return summary


def render_markdown(summary: dict) -> str:
    lines = [
        "# JVM Runtime Monitoring Summary",
        "",
        f"- Input: `{summary['input']}`",
        f"- Files scanned: {summary['file_count']}",
        "",
        "## Parsed Evidence",
        "",
    ]

    classified = summary["classified_files"]
    if classified:
        for key in sorted(classified):
            lines.append(f"- {key}: {len(classified[key])} file(s)")
    else:
        lines.append("- No recognized JVM monitoring artifact names were found.")
    lines.append("")

    jstat = summary["jstat"]
    if jstat.get("rows"):
        lines.extend(["## jstat GC Summary", "", "| Column | Min | Max | Avg | Last |", "| --- | ---: | ---: | ---: | ---: |"])
        for column, stats in sorted(jstat.get("percent", {}).items()):
            lines.append(f"| {column} | {stats['min']} | {stats['max']} | {stats['avg']} | {stats['last']} |")
        lines.append("")
        if jstat.get("deltas"):
            lines.extend(["| Counter | Delta |", "| --- | ---: |"])
            for column, delta in sorted(jstat["deltas"].items()):
                lines.append(f"| {column} | {delta} |")
            lines.append("")

    threads = summary["threads"]
    if threads.get("total"):
        lines.extend(["## Thread State Markers", "", "| State | Count |", "| --- | ---: |"])
        for state, count in sorted(threads["total"].items()):
            lines.append(f"| {state} | {count} |")
        lines.append("")

    if summary["heap_markers"]:
        lines.extend(["## Heap Markers", ""])
        for item in summary["heap_markers"][:5]:
            lines.append(f"- `{item['file']}`")
            lines.extend(f"  - {marker}" for marker in item["markers"][:6])
        lines.append("")

    if summary["nmt_markers"]:
        lines.extend(["## Native Memory Markers", ""])
        for item in summary["nmt_markers"][:5]:
            lines.append(f"- `{item['file']}`")
            lines.extend(f"  - {marker}" for marker in item["markers"][:6])
        lines.append("")

    lines.extend(["## Findings", ""])
    lines.extend(f"- {finding}" for finding in summary["findings"])
    lines.extend(
        [
            "",
            "## Next Checks",
            "",
            "- Correlate GC and thread evidence with request latency, CPU, container memory, and deployment events.",
            "- Treat this as a first-pass summary; inspect raw artifacts before making production changes.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Monitoring artifact file or directory")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args()

    summary = summarize(Path(args.path))
    output = json.dumps(summary, indent=2) + "\n" if args.format == "json" else render_markdown(summary)
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
