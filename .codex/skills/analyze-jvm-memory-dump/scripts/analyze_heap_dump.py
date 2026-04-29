#!/usr/bin/env python3
"""Run or prepare direct JVM dump analysis with local tools."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_REPORTS = [
    "org.eclipse.mat.api:suspects",
    "org.eclipse.mat.api:overview",
    "org.eclipse.mat.api:top_components",
]


def human_size(num: int | None) -> str:
    if num is None:
        return ""
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num} B"


def read_head(path: Path, size: int = 4096) -> bytes:
    with path.open("rb") as fh:
        return fh.read(size)


def dump_kind(path: Path, head: bytes) -> str:
    suffix = path.suffix.lower()
    if head.startswith(b"JAVA PROFILE ") or suffix == ".hprof":
        return "hprof"
    if head.startswith(b"\x7fELF") or suffix in {".core", ".dmp"}:
        return "core_dump"
    return "unknown_dump"


def dump_header(head: bytes) -> str:
    if head.startswith(b"JAVA PROFILE "):
        return head.split(b"\x00", 1)[0].decode("ascii", errors="replace")
    if head.startswith(b"\x7fELF"):
        return "ELF binary/core"
    return "unknown"


def find_parse_heap_dump(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for name in ("ParseHeapDump.sh", "parse_heap_dump"):
        found = shutil.which(name)
        if found:
            return found
    common_paths = [
        "/Applications/mat/ParseHeapDump.sh",
        "/Applications/MemoryAnalyzer.app/Contents/Eclipse/ParseHeapDump.sh",
        "/Applications/Eclipse Memory Analyzer.app/Contents/Eclipse/ParseHeapDump.sh",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path
    return None


def hprof_command(parse_heap_dump: str, dump: Path, reports: list[str], mat_xmx: str) -> list[str]:
    return [parse_heap_dump, str(dump), *reports, "-vmargs", f"-Xmx{mat_xmx}"]


def suggested_commands(kind: str, dump: Path, mat_xmx: str) -> list[str]:
    if kind == "hprof":
        reports = " ".join(DEFAULT_REPORTS)
        return [
            f"ParseHeapDump.sh {dump} {reports} -vmargs -Xmx{mat_xmx}",
            f"jvisualvm --openfile {dump}",
        ]
    if kind == "core_dump":
        return [
            f"jhsdb jmap --binaryheap --dumpfile heap-from-core.hprof --exe <path-to-java> --core {dump}",
            f"jhsdb jstack --exe <path-to-java> --core {dump}",
            f"gdb <path-to-java> {dump}",
        ]
    return []


def run_command(command: list[str], out_dir: Path, timeout: int | None) -> dict[str, Any]:
    started = dt.datetime.now().isoformat(timespec="seconds")
    proc = subprocess.run(
        command,
        cwd=str(out_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    stdout_path = out_dir / "heap-dump-analysis.stdout.txt"
    stderr_path = out_dir / "heap-dump-analysis.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(proc.stderr, encoding="utf-8", errors="replace")
    return {
        "started": started,
        "finished": dt.datetime.now().isoformat(timespec="seconds"),
        "returncode": proc.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }


def list_outputs(out_dir: Path) -> list[str]:
    outputs: list[str] = []
    for child in sorted(out_dir.iterdir()):
        if child.is_file() and child.name != "analysis.json":
            outputs.append(str(child))
    return outputs


def to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# JVM Dump Direct Analysis")
    lines.append("")
    lines.append(f"Dump: `{payload['dump']['path']}`")
    lines.append(f"Type: {payload['dump']['type']}")
    lines.append(f"Size: {payload['dump']['size_human']}")
    lines.append(f"Header: {payload['dump']['header']}")
    lines.append("")
    if payload.get("command"):
        lines.append("## Command")
        lines.append("")
        lines.append("```bash")
        lines.append(" ".join(payload["command"]))
        lines.append("```")
        lines.append("")
    if payload.get("run"):
        run = payload["run"]
        lines.append("## Run Result")
        lines.append("")
        lines.append(f"Return code: {run['returncode']}")
        lines.append(f"Stdout: `{run['stdout']}`")
        lines.append(f"Stderr: `{run['stderr']}`")
        lines.append("")
    if payload.get("outputs"):
        lines.append("## Outputs")
        lines.append("")
        for output in payload["outputs"]:
            lines.append(f"- `{output}`")
        lines.append("")
    if payload.get("suggested_commands"):
        lines.append("## Suggested Commands")
        lines.append("")
        for command in payload["suggested_commands"]:
            lines.append(f"- `{command}`")
        lines.append("")
    if payload.get("notes"):
        lines.append("## Notes")
        lines.append("")
        for note in payload["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run or prepare direct analysis for JVM HPROF/native dump files.")
    parser.add_argument("dump", help="Heap dump or native/core dump file")
    parser.add_argument("--out-dir", default="/tmp/jvm-heap-dump-analysis", help="Directory for reports and command logs")
    parser.add_argument("--parse-heap-dump", help="Path to Eclipse MAT ParseHeapDump.sh")
    parser.add_argument("--mat-xmx", default="8g", help="Heap size for MAT, for example 8g or 16g")
    parser.add_argument("--reports", default=",".join(DEFAULT_REPORTS), help="Comma-separated MAT report IDs")
    parser.add_argument("--dry-run", action="store_true", help="Do not execute MAT; only print command and metadata")
    parser.add_argument("--timeout", type=int, help="Optional timeout in seconds for MAT")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    dump = Path(args.dump).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    head = read_head(dump)
    kind = dump_kind(dump, head)
    reports = [report.strip() for report in args.reports.split(",") if report.strip()]
    parse_heap_dump = find_parse_heap_dump(args.parse_heap_dump)
    payload: dict[str, Any] = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "dump": {
            "path": str(dump),
            "type": kind,
            "size_bytes": dump.stat().st_size,
            "size_human": human_size(dump.stat().st_size),
            "header": dump_header(head),
        },
        "out_dir": str(out_dir),
        "notes": [],
    }

    if kind == "hprof" and parse_heap_dump:
        command = hprof_command(parse_heap_dump, dump, reports, args.mat_xmx)
        payload["command"] = command
        if args.dry_run:
            payload["notes"].append("Dry run: MAT command was not executed.")
        else:
            payload["run"] = run_command(command, out_dir, args.timeout)
            payload["outputs"] = list_outputs(out_dir)
    elif kind == "hprof":
        payload["notes"].append("Eclipse MAT ParseHeapDump.sh was not found on PATH or common application paths.")
        payload["suggested_commands"] = suggested_commands(kind, dump, args.mat_xmx)
    elif kind == "core_dump":
        payload["notes"].append("Native/core dump detected. Use a matching JDK/JVM binary and symbols where possible.")
        payload["suggested_commands"] = suggested_commands(kind, dump, args.mat_xmx)
    else:
        payload["notes"].append("Dump type is unknown. Verify whether this is HPROF, IBM PHD, or native core dump.")
        payload["suggested_commands"] = suggested_commands("hprof", dump, args.mat_xmx)

    analysis_json = out_dir / "analysis.json"
    payload["analysis_json"] = str(analysis_json)
    analysis_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.format == "json":
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(to_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
